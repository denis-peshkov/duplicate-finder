"""
Экран результатов поиска дубликатов (как в референсе).
"""

from __future__ import annotations

import logging
import queue
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import Listbox, Menu, messagebox
from typing import Callable, Optional

import customtkinter as ctk

from src.config.app_info import HELP_RESULTS
from src.core.deleter import DeleteProgress, DeleteResult, delete_to_recycle_bin
from src.core.models import DuplicateGroup, FileEntry, ScanResult
from src.ui.about_window import show_about
from src.ui.delete_progress_window import DeleteProgressWindow
from src.ui.info_dialog import show_info_dialog
from src.utils.formatters import format_count

logger = logging.getLogger(__name__)

FILE_FONT_SIZE = 14


def _format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} bytes"
    units = ["KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        size /= 1024
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
    return f"{num_bytes} bytes"


def _group_title(group: DuplicateGroup) -> str:
    if group.files:
        name = group.files[0].path.name
    else:
        name = group.key[:40]
    return f"({format_count(len(group.files))} found) {name}"


class PageResults(ctk.CTkFrame):
    """Страница просмотра и удаления найденных дубликатов."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_back: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.on_back = on_back
        self.on_cancel = on_cancel
        self._result: ScanResult | None = None
        self._selected_group_index: int = -1
        self._row_vars: dict[Path, ctk.BooleanVar] = {}
        self._entry_by_path: dict[Path, FileEntry] = {}
        self._checked_paths: set[Path] = set()
        self._file_rows: list[ctk.CTkFrame] = []
        self._table_font = ctk.CTkFont(size=FILE_FONT_SIZE)
        self._delete_mode = ctk.StringVar(value="custom")
        self._delete_queue: queue.Queue = queue.Queue()
        self._delete_thread: threading.Thread | None = None
        self._delete_cancel = threading.Event()
        self._delete_progress: DeleteProgressWindow | None = None

        self._create_widgets()
        self.after(100, self._process_delete_queue)

    def _create_widgets(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent", height=52)
        footer.pack(side="bottom", fill="x", padx=12, pady=(0, 10))
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="?",
            width=28,
            height=28,
            command=self._show_results_help,
        ).pack(side="left")

        ctk.CTkButton(
            footer,
            text="About",
            width=70,
            height=28,
            command=self._show_about,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            footer,
            text="Cancel",
            width=100,
            command=self._handle_cancel,
        ).pack(side="right", padx=(8, 0))

        self.next_btn = ctk.CTkButton(
            footer,
            text="Next",
            width=100,
            command=self._handle_next,
        )
        self.next_btn.pack(side="right", padx=(8, 0))

        self.back_btn = ctk.CTkButton(
            footer,
            text="Back",
            width=100,
            command=self._handle_back,
        )
        self.back_btn.pack(side="right")

        content = ctk.CTkFrame(self)
        content.pack(side="top", fill="both", expand=True, padx=12, pady=(12, 8))

        self.summary_label = ctk.CTkLabel(
            content,
            text="Sets of duplicates: 0",
            font=ctk.CTkFont(size=14),
            anchor="w",
        )
        self.summary_label.pack(fill="x", padx=10, pady=(10, 6))

        sets_frame = ctk.CTkFrame(content)
        sets_frame.pack(fill="x", padx=10, pady=(0, 8))

        list_host = ctk.CTkFrame(sets_frame, fg_color="#1a1a1a")
        list_host.pack(fill="both", expand=True, padx=4, pady=4)

        self.sets_list = Listbox(
            list_host,
            activestyle="dotbox",
            exportselection=False,
            bg="#1a1a1a",
            fg="#e8e8e8",
            selectbackground="#3a3a3a",
            selectforeground="#ffffff",
            highlightthickness=0,
            borderwidth=0,
            font=("Segoe UI", FILE_FONT_SIZE),
            height=10,
        )
        self.sets_list.pack(side="left", fill="both", expand=True)
        sets_scroll = ctk.CTkScrollbar(list_host, command=self.sets_list.yview)
        sets_scroll.pack(side="right", fill="y")
        self.sets_list.configure(yscrollcommand=sets_scroll.set)
        self.sets_list.bind("<<ListboxSelect>>", self._on_set_selected)

        # Режим удаления — только для two lists
        self.delete_mode_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.delete_mode_frame.pack(fill="x", padx=10, pady=(4, 0))

        ctk.CTkRadioButton(
            self.delete_mode_frame,
            text="Custom",
            variable=self._delete_mode,
            value="custom",
            command=self._on_delete_mode_change,
        ).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(
            self.delete_mode_frame,
            text="Delete from File List 1",
            variable=self._delete_mode,
            value="list1",
            command=self._on_delete_mode_change,
        ).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(
            self.delete_mode_frame,
            text="Delete from File List 2",
            variable=self._delete_mode,
            value="list2",
            command=self._on_delete_mode_change,
        ).pack(side="left")

        self.hint_label = ctk.CTkLabel(
            content,
            text=(
                "Select the checkbox of the items you wish to delete, "
                "or right-click for more options, including Rename."
            ),
            anchor="w",
            justify="left",
            wraplength=900,
        )
        self.hint_label.pack(fill="x", padx=10, pady=(4, 6))

        # По умолчанию скрыт — показывается только в two_lists
        self.delete_mode_frame.pack_forget()

        table_frame = ctk.CTkFrame(content)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        header = ctk.CTkFrame(table_frame, fg_color="transparent", height=28)
        header.pack(fill="x", padx=4, pady=(6, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="", width=28).pack(side="left")
        ctk.CTkLabel(
            header, text="Filename", width=180, anchor="w", font=self._table_font
        ).pack(side="left")
        ctk.CTkLabel(
            header, text="File Size", width=110, anchor="w", font=self._table_font
        ).pack(side="left")
        ctk.CTkLabel(
            header, text="Original Path", anchor="w", font=self._table_font
        ).pack(side="left", fill="x", expand=True)

        self.table_scroll = ctk.CTkScrollableFrame(table_frame, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 6))

    def show_results(self, result: ScanResult) -> None:
        """Отобразить результаты сканирования."""
        self._result = result
        self._selected_group_index = -1
        self._row_vars.clear()
        self._entry_by_path.clear()
        self._checked_paths.clear()
        self._clear_table()
        self.sets_list.delete(0, "end")
        self._delete_mode.set("custom")

        if result.search_mode == "two_lists":
            self.delete_mode_frame.pack(fill="x", padx=10, pady=(4, 0), before=self.hint_label)
        else:
            self.delete_mode_frame.pack_forget()

        if result.canceled:
            self.summary_label.configure(text="Sets of duplicates: 0 (canceled)")
            return

        self.summary_label.configure(
            text=f"Sets of duplicates: {format_count(len(result.groups))}"
        )

        for group in result.groups:
            self.sets_list.insert("end", _group_title(group))

        if result.groups:
            self.sets_list.selection_set(0)
            self.sets_list.activate(0)
            self._show_group(0)
        else:
            empty = ctk.CTkLabel(
                self.table_scroll,
                text="No duplicates found.",
                text_color="gray70",
                font=self._table_font,
            )
            empty.pack(anchor="w", pady=8)
            self._file_rows.append(empty)  # type: ignore[arg-type]

    def _on_set_selected(self, _event: object = None) -> None:
        selection = self.sets_list.curselection()
        if not selection:
            return
        self._show_group(int(selection[0]))

    def _show_group(self, index: int) -> None:
        if not self._result or index < 0 or index >= len(self._result.groups):
            return
        self._selected_group_index = index
        self._render_table(self._result.groups[index])

    def _clear_table(self) -> None:
        for widget in self.table_scroll.winfo_children():
            widget.destroy()
        self._file_rows.clear()

    def _render_table(self, group: DuplicateGroup) -> None:
        self._clear_table()
        self._row_vars.clear()
        self._entry_by_path.clear()

        for entry in group.files:
            row = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            self._file_rows.append(row)

            var = ctk.BooleanVar(value=entry.path in self._checked_paths)
            self._row_vars[entry.path] = var
            self._entry_by_path[entry.path] = entry
            var.trace_add(
                "write",
                lambda *_args, p=entry.path, v=var: self._on_checkbox_changed(p, v),
            )

            ctk.CTkCheckBox(row, text="", variable=var, width=28).pack(side="left")

            name_label = ctk.CTkLabel(
                row,
                text=entry.path.name,
                width=180,
                anchor="w",
                font=self._table_font,
            )
            name_label.pack(side="left")

            size_label = ctk.CTkLabel(
                row,
                text=_format_size(entry.size),
                width=110,
                anchor="w",
                font=self._table_font,
            )
            size_label.pack(side="left")

            path_label = ctk.CTkLabel(
                row,
                text=str(entry.path),
                anchor="w",
                justify="left",
                font=self._table_font,
            )
            path_label.pack(side="left", fill="x", expand=True)

            for widget in (row, name_label, size_label, path_label):
                widget.bind("<Button-3>", lambda e, p=entry.path: self._show_context_menu(e, p))

    def _on_checkbox_changed(self, path: Path, var: ctk.BooleanVar) -> None:
        if var.get():
            self._checked_paths.add(path)
        else:
            self._checked_paths.discard(path)

    def _on_delete_mode_change(self) -> None:
        """Custom — сброс всех выделений.
        List 1/2 — сброс и пометка всех дубликатов из соответствующего списка.
        """
        if not self._result:
            return

        mode = self._delete_mode.get()
        self._checked_paths.clear()

        if mode in ("list1", "list2") and self._result.search_mode == "two_lists":
            source = mode
            for group in self._result.groups:
                for entry in group.files:
                    if entry.source == source:
                        self._checked_paths.add(entry.path)

        self._sync_visible_checkboxes()

    def _sync_visible_checkboxes(self) -> None:
        for path, var in self._row_vars.items():
            desired = path in self._checked_paths
            if bool(var.get()) != desired:
                var.set(desired)

    def _show_context_menu(self, event: object, path: Path) -> None:
        menu = Menu(self, tearoff=0)
        menu.add_command(label="Open folder", command=lambda: self._open_folder(path))
        menu.add_command(label="Rename...", command=lambda: self._rename_file(path))
        menu.add_separator()
        menu.add_command(
            label="Select for delete",
            command=lambda: self._set_checked(path, True),
        )
        menu.add_command(
            label="Keep (uncheck)",
            command=lambda: self._set_checked(path, False),
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)  # type: ignore[attr-defined]
        finally:
            menu.grab_release()

    def _set_checked(self, path: Path, value: bool) -> None:
        if value:
            self._checked_paths.add(path)
        else:
            self._checked_paths.discard(path)
        var = self._row_vars.get(path)
        if var is not None and bool(var.get()) != value:
            var.set(value)

    def _open_folder(self, path: Path) -> None:
        folder = path.parent if path.exists() else path.parent
        try:
            if sys.platform.startswith("win"):
                subprocess.run(["explorer", "/select,", str(path)], check=False)
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except OSError as exc:
            messagebox.showerror("Duplicate Finder", f"Cannot open folder:\n{exc}")

    def _rename_file(self, path: Path) -> None:
        dialog = ctk.CTkInputDialog(text=f"New name for:\n{path.name}", title="Rename")
        new_name = dialog.get_input()
        if not new_name or new_name == path.name:
            return
        target = path.with_name(new_name)
        try:
            path.rename(target)
        except OSError as exc:
            messagebox.showerror("Rename failed", str(exc))
            return

        if self._result and self._selected_group_index >= 0:
            group = self._result.groups[self._selected_group_index]
            for entry in group.files:
                if entry.path == path:
                    entry.path = target
            if group.keep_suggestion == path:
                group.keep_suggestion = target
            if path in self._checked_paths:
                self._checked_paths.discard(path)
                self._checked_paths.add(target)
            self.sets_list.delete(self._selected_group_index)
            self.sets_list.insert(self._selected_group_index, _group_title(group))
            self.sets_list.selection_set(self._selected_group_index)
            self._show_group(self._selected_group_index)

    def _collect_selected_paths(self) -> list[Path]:
        """Все отмеченные файлы по всем сетам."""
        # синхронизируем видимые чекбоксы на случай ручного изменения
        for path, var in self._row_vars.items():
            if var.get():
                self._checked_paths.add(path)
            else:
                self._checked_paths.discard(path)
        return sorted(self._checked_paths, key=lambda p: str(p).lower())

    def _handle_next(self) -> None:
        if not self._result:
            return
        if self._delete_thread and self._delete_thread.is_alive():
            return

        selected = self._collect_selected_paths()
        if not selected:
            messagebox.showinfo(
                "Duplicate Finder",
                "Select at least one file to delete, or go Back.",
            )
            return

        preview = "\n".join(str(path) for path in selected[:10])
        extra = (
            f"\n... and {format_count(len(selected) - 10)} more"
            if len(selected) > 10
            else ""
        )
        confirmed = messagebox.askyesno(
            "Confirm deletion",
            f"Move {format_count(len(selected))} file(s) to Recycle Bin?\n\n{preview}{extra}",
        )
        if not confirmed:
            return

        self._start_delete(selected)

    def _start_delete(self, selected: list[Path]) -> None:
        self._delete_cancel.clear()
        self.next_btn.configure(state="disabled")
        self.back_btn.configure(state="disabled")

        self._delete_progress = DeleteProgressWindow(
            self.winfo_toplevel(),
            total=len(selected),
            on_cancel=self._delete_cancel.set,
        )
        self._delete_progress.update()

        self._delete_thread = threading.Thread(
            target=self._delete_worker,
            args=(selected,),
            daemon=True,
            name="duplicate-delete",
        )
        self._delete_thread.start()

    def _delete_worker(self, selected: list[Path]) -> None:
        try:
            def progress_callback(progress: DeleteProgress) -> None:
                if self._delete_queue.qsize() < 64:
                    self._delete_queue.put(("progress", progress))

            result = delete_to_recycle_bin(
                selected,
                progress_callback=progress_callback,
                cancel_check=self._delete_cancel.is_set,
            )
            self._delete_queue.put(("done", result))
        except Exception as exc:
            logger.exception("Delete failed")
            self._delete_queue.put(("error", str(exc)))

    def _process_delete_queue(self) -> None:
        try:
            while True:
                message_type, payload = self._delete_queue.get_nowait()
                if message_type == "progress" and self._delete_progress:
                    self._delete_progress.update_progress(payload)
                elif message_type == "done":
                    self._on_delete_done(payload)
                elif message_type == "error":
                    self._on_delete_error(str(payload))
        except queue.Empty:
            pass
        self.after(80, self._process_delete_queue)

    def _close_delete_progress(self) -> None:
        if self._delete_progress is not None:
            try:
                self._delete_progress.finish()
                self._delete_progress.destroy()
            except Exception:  # noqa: BLE001
                pass
            self._delete_progress = None
        self.next_btn.configure(state="normal")
        self.back_btn.configure(state="normal")

    def _on_delete_done(self, result: DeleteResult) -> None:
        self._close_delete_progress()

        if result.canceled:
            messagebox.showinfo(
                "Duplicate Finder",
                (
                    f"Deletion canceled.\n"
                    f"Moved: {format_count(len(result.deleted))}\n"
                    f"Remaining were kept."
                ),
            )
        elif result.failed:
            failed_text = "\n".join(
                f"{path}: {error}" for path, error in result.failed[:5]
            )
            messagebox.showwarning(
                "Partial deletion",
                (
                    f"Deleted: {format_count(len(result.deleted))}\n"
                    f"Failed: {format_count(len(result.failed))}\n\n{failed_text}"
                ),
            )
        else:
            messagebox.showinfo(
                "Duplicate Finder",
                f"Moved {format_count(len(result.deleted))} file(s) to Recycle Bin.",
            )

        if result.deleted:
            self._remove_deleted_files(set(result.deleted))

    def _on_delete_error(self, message: str) -> None:
        self._close_delete_progress()
        messagebox.showerror("Delete error", message)

    def _remove_deleted_files(self, deleted: set[Path]) -> None:
        if not self._result:
            return

        new_groups: list[DuplicateGroup] = []
        for group in self._result.groups:
            remaining = [entry for entry in group.files if entry.path not in deleted]
            if len(remaining) >= 2:
                new_groups.append(DuplicateGroup(key=group.key, files=remaining))

        self._result.groups = new_groups
        previous = self._selected_group_index
        saved_mode = self._delete_mode.get()
        self.show_results(self._result)
        if self._result.search_mode == "two_lists":
            self._delete_mode.set(saved_mode)
            self._on_delete_mode_change()
        if self._result.groups:
            index = min(max(previous, 0), len(self._result.groups) - 1)
            self.sets_list.selection_clear(0, "end")
            self.sets_list.selection_set(index)
            self.sets_list.see(index)
            self._show_group(index)

    def _handle_back(self) -> None:
        if self.on_back:
            self.on_back()

    def _handle_cancel(self) -> None:
        if self.on_cancel:
            self.on_cancel()

    def _show_about(self) -> None:
        show_about(self)

    def _show_results_help(self) -> None:
        show_info_dialog(self, "Results", HELP_RESULTS, width=520)
