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
from src.core.deleter import DeleteProgress, DeleteResult, delete_to_recycle_bin, remove_empty_folders
from src.core.models import DuplicateGroup, FileEntry, ScanResult
from src.ui.about_window import show_about
from src.ui.delete_progress_window import DeleteProgressWindow
from src.ui.info_dialog import show_info_dialog
from src.utils.formatters import format_count

logger = logging.getLogger(__name__)

FILE_FONT_SIZE = 14
CHECK_COL_WIDTH = 28
NAME_COL_DEFAULT = 220
SIZE_COL_DEFAULT = 110
NAME_COL_MIN = 80
SIZE_COL_MIN = 70
PATH_COL_MIN = 120


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


def _ellipsize(text: str, width_px: int, font_size: int = FILE_FONT_SIZE) -> str:
    """Обрезать текст под ширину колонки с многоточием."""
    if width_px <= 0:
        return ""
    # Приблизительно: ~0.55em на символ для Segoe UI
    max_chars = max(4, int(width_px / max(font_size * 0.55, 1)))
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return "…"
    return text[: max_chars - 1] + "…"


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
        self._name_col_width = NAME_COL_DEFAULT
        self._size_col_width = SIZE_COL_DEFAULT
        self._resize_col: str | None = None
        self._resize_start_x = 0
        self._resize_start_width = 0
        self._applying_widths = False
        self._width_apply_after: str | None = None
        self._header_name_label: ctk.CTkLabel | None = None
        self._header_size_label: ctk.CTkLabel | None = None
        self._row_name_cells: list[tuple[ctk.CTkFrame, ctk.CTkLabel, str]] = []
        self._row_size_cells: list[tuple[ctk.CTkFrame, ctk.CTkLabel]] = []
        self._row_path_cells: list[tuple[ctk.CTkFrame, ctk.CTkLabel, str]] = []
        self._delete_mode = ctk.StringVar(value="custom")
        self._clean_empty_folders = ctk.BooleanVar(value=False)
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
        self.hint_label.pack(fill="x", padx=10, pady=(4, 4))

        ctk.CTkCheckBox(
            content,
            text="Clean empty folders in target location",
            variable=self._clean_empty_folders,
        ).pack(anchor="w", padx=10, pady=(0, 6))

        # По умолчанию скрыт — показывается только в two_lists
        self.delete_mode_frame.pack_forget()

        table_frame = ctk.CTkFrame(content)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._table_header = ctk.CTkFrame(table_frame, fg_color="transparent", height=28)
        self._table_header.pack(fill="x", padx=4, pady=(6, 0))
        self._table_header.pack_propagate(False)
        self._build_table_header()

        self.table_scroll = ctk.CTkScrollableFrame(table_frame, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 6))
        self.table_scroll.bind("<Configure>", self._schedule_column_widths)

    def _build_table_header(self) -> None:
        """Заголовок таблицы с ручками ресайза колонок."""
        for child in self._table_header.winfo_children():
            child.destroy()

        ctk.CTkLabel(self._table_header, text="", width=CHECK_COL_WIDTH).pack(side="left")

        name_wrap = ctk.CTkFrame(
            self._table_header,
            width=self._name_col_width,
            fg_color="transparent",
        )
        name_wrap.pack(side="left", fill="y")
        name_wrap.pack_propagate(False)
        self._header_name_wrap = name_wrap
        self._header_name_label = ctk.CTkLabel(
            name_wrap,
            text="Filename",
            anchor="w",
            font=self._table_font,
        )
        self._header_name_label.pack(side="left", fill="both", expand=True)

        self._make_resize_grip("name").pack(side="left", fill="y", padx=(0, 2))

        size_wrap = ctk.CTkFrame(
            self._table_header,
            width=self._size_col_width,
            fg_color="transparent",
        )
        size_wrap.pack(side="left", fill="y")
        size_wrap.pack_propagate(False)
        self._header_size_wrap = size_wrap
        self._header_size_label = ctk.CTkLabel(
            size_wrap,
            text="File Size",
            anchor="w",
            font=self._table_font,
        )
        self._header_size_label.pack(side="left", fill="both", expand=True)

        self._make_resize_grip("size").pack(side="left", fill="y", padx=(0, 2))

        path_wrap = ctk.CTkFrame(self._table_header, fg_color="transparent")
        path_wrap.pack(side="left", fill="both", expand=True)
        self._header_path_wrap = path_wrap
        ctk.CTkLabel(
            path_wrap,
            text="Original Path",
            anchor="w",
            font=self._table_font,
        ).pack(side="left", fill="both", expand=True)

    def _make_resize_grip(self, column: str) -> ctk.CTkFrame:
        grip = ctk.CTkFrame(
            self._table_header,
            width=4,
            fg_color=("gray70", "gray40"),
            cursor="size_we",
        )
        grip.bind("<ButtonPress-1>", lambda e, c=column: self._start_col_resize(e, c))
        grip.bind("<B1-Motion>", self._on_col_resize)
        grip.bind("<ButtonRelease-1>", self._end_col_resize)
        return grip

    def _start_col_resize(self, event: object, column: str) -> None:
        self._resize_col = column
        self._resize_start_x = int(getattr(event, "x_root", 0))
        self._resize_start_width = (
            self._name_col_width if column == "name" else self._size_col_width
        )

    def _on_col_resize(self, event: object) -> None:
        if not self._resize_col:
            return
        delta = int(getattr(event, "x_root", 0)) - self._resize_start_x
        if self._resize_col == "name":
            self._name_col_width = max(NAME_COL_MIN, self._resize_start_width + delta)
        else:
            self._size_col_width = max(SIZE_COL_MIN, self._resize_start_width + delta)
        self._apply_column_widths()

    def _end_col_resize(self, _event: object = None) -> None:
        self._resize_col = None

    def _schedule_column_widths(self, _event: object = None) -> None:
        """Отложенное обновление — без рекурсии от Configure."""
        if self._applying_widths or self._resize_col:
            return
        if self._width_apply_after is not None:
            try:
                self.after_cancel(self._width_apply_after)
            except Exception:  # noqa: BLE001
                pass
        self._width_apply_after = self.after(16, self._apply_column_widths)

    def _path_col_width(self) -> int:
        try:
            total = int(self.table_scroll.winfo_width())
        except Exception:  # noqa: BLE001
            total = 800
        if total <= 1:
            total = 800
        used = CHECK_COL_WIDTH + self._name_col_width + self._size_col_width + 16
        return max(PATH_COL_MIN, total - used)

    def _alive(self, widget: object) -> bool:
        try:
            return bool(widget.winfo_exists())  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            return False

    def _apply_column_widths(self) -> None:
        """Обновить ширины ячеек и переобрезать текст под новый размер."""
        self._width_apply_after = None
        if self._applying_widths:
            return
        self._applying_widths = True
        try:
            path_width = self._path_col_width()

            if hasattr(self, "_header_name_wrap") and self._alive(self._header_name_wrap):
                self._header_name_wrap.configure(width=self._name_col_width)
            if hasattr(self, "_header_size_wrap") and self._alive(self._header_size_wrap):
                self._header_size_wrap.configure(width=self._size_col_width)

            for frame, label, full in list(self._row_name_cells):
                if not self._alive(frame) or not self._alive(label):
                    continue
                frame.configure(width=self._name_col_width)
                label.configure(text=_ellipsize(full, self._name_col_width))

            for frame, _label in list(self._row_size_cells):
                if not self._alive(frame):
                    continue
                frame.configure(width=self._size_col_width)

            for frame, label, full in list(self._row_path_cells):
                if not self._alive(frame) or not self._alive(label):
                    continue
                frame.configure(width=path_width)
                label.configure(text=_ellipsize(full, path_width))
        except Exception:  # noqa: BLE001
            logger.exception("Ошибка при обновлении ширины колонок")
        finally:
            self._applying_widths = False

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
        self._row_name_cells.clear()
        self._row_size_cells.clear()
        self._row_path_cells.clear()

    def _render_table(self, group: DuplicateGroup) -> None:
        self._clear_table()
        self._row_vars.clear()
        self._entry_by_path.clear()
        path_width = self._path_col_width()

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

            ctk.CTkCheckBox(row, text="", variable=var, width=CHECK_COL_WIDTH).pack(
                side="left"
            )

            name_full = entry.path.name
            name_frame = ctk.CTkFrame(
                row,
                width=self._name_col_width,
                fg_color="transparent",
            )
            name_frame.pack(side="left", fill="y")
            name_frame.pack_propagate(False)
            name_label = ctk.CTkLabel(
                name_frame,
                text=_ellipsize(name_full, self._name_col_width),
                anchor="w",
                font=self._table_font,
            )
            name_label.pack(side="left", fill="both", expand=True)
            self._row_name_cells.append((name_frame, name_label, name_full))

            size_frame = ctk.CTkFrame(
                row,
                width=self._size_col_width,
                fg_color="transparent",
            )
            size_frame.pack(side="left", fill="y")
            size_frame.pack_propagate(False)
            size_label = ctk.CTkLabel(
                size_frame,
                text=_format_size(entry.size),
                anchor="w",
                font=self._table_font,
            )
            size_label.pack(side="left", fill="both", expand=True)
            self._row_size_cells.append((size_frame, size_label))

            path_full = str(entry.path)
            path_frame = ctk.CTkFrame(
                row,
                width=path_width,
                fg_color="transparent",
            )
            path_frame.pack(side="left", fill="y")
            path_frame.pack_propagate(False)
            path_label = ctk.CTkLabel(
                path_frame,
                text=_ellipsize(path_full, path_width),
                anchor="w",
                font=self._table_font,
            )
            path_label.pack(side="left", fill="both", expand=True)
            self._row_path_cells.append((path_frame, path_label, path_full))

            for widget in (row, name_label, size_label, path_label):
                widget.bind(
                    "<Button-3>",
                    lambda e, p=entry.path: self._show_context_menu(e, p),
                )

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
        clean_empty = self._clean_empty_folders.get()
        if not selected and not clean_empty:
            messagebox.showinfo(
                "Duplicate Finder",
                "Select at least one file to delete, enable empty-folder cleanup, or go Back.",
            )
            return

        if selected:
            preview = "\n".join(str(path) for path in selected[:10])
            extra = (
                f"\n... and {format_count(len(selected) - 10)} more"
                if len(selected) > 10
                else ""
            )
            clean_note = (
                "\n\nEmpty folders under search paths will also be cleaned."
                if clean_empty
                else ""
            )
            confirmed = messagebox.askyesno(
                "Confirm deletion",
                (
                    f"Move {format_count(len(selected))} file(s) to Recycle Bin?\n\n"
                    f"{preview}{extra}{clean_note}"
                ),
            )
        else:
            confirmed = messagebox.askyesno(
                "Confirm cleanup",
                "Clean empty folders under all search paths?",
            )
        if not confirmed:
            return

        self._start_delete(selected, clean_empty=clean_empty)

    def _start_delete(self, selected: list[Path], *, clean_empty: bool) -> None:
        self._delete_cancel.clear()
        self.next_btn.configure(state="disabled")
        self.back_btn.configure(state="disabled")

        self._delete_progress = DeleteProgressWindow(
            self.winfo_toplevel(),
            total=max(len(selected), 1),
            on_cancel=self._delete_cancel.set,
        )
        self._delete_progress.update()

        self._delete_thread = threading.Thread(
            target=self._delete_worker,
            args=(selected, clean_empty),
            daemon=True,
            name="duplicate-delete",
        )
        self._delete_thread.start()

    def _delete_worker(self, selected: list[Path], clean_empty: bool) -> None:
        try:
            def progress_callback(progress: DeleteProgress) -> None:
                if self._delete_queue.qsize() < 64:
                    self._delete_queue.put(("progress", progress))

            if selected:
                result = delete_to_recycle_bin(
                    selected,
                    progress_callback=progress_callback,
                    cancel_check=self._delete_cancel.is_set,
                )
            else:
                result = DeleteResult(deleted=[], failed=[], canceled=False)

            if clean_empty and not result.canceled:
                roots = self._result.search_roots if self._result else []
                folders_removed, folders_failed = remove_empty_folders(
                    roots=roots,
                    cancel_check=self._delete_cancel.is_set,
                )
                result.folders_removed = folders_removed
                result.folders_failed = folders_failed
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

        folders_note = ""
        if result.folders_removed or result.folders_failed:
            folders_note = (
                f"\nEmpty folders removed: {format_count(len(result.folders_removed))}"
            )
            if result.folders_failed:
                folders_note += (
                    f"\nEmpty folders failed: {format_count(len(result.folders_failed))}"
                )

        if result.canceled:
            messagebox.showinfo(
                "Duplicate Finder",
                (
                    f"Deletion canceled.\n"
                    f"Moved: {format_count(len(result.deleted))}\n"
                    f"Remaining were kept."
                    f"{folders_note}"
                ),
            )
        elif result.failed or result.folders_failed:
            failed_items = list(result.failed) + list(result.folders_failed)
            failed_text = "\n".join(
                f"{path}: {error}" for path, error in failed_items[:5]
            )
            messagebox.showwarning(
                "Partial deletion",
                (
                    f"Deleted: {format_count(len(result.deleted))}\n"
                    f"Failed: {format_count(len(result.failed))}"
                    f"{folders_note}\n\n{failed_text}"
                ),
            )
        else:
            if result.deleted:
                message = (
                    f"Moved {format_count(len(result.deleted))} file(s) to Recycle Bin."
                    f"{folders_note}"
                )
            elif result.folders_removed:
                message = (
                    f"Removed {format_count(len(result.folders_removed))} empty folder(s)."
                )
            else:
                message = f"Nothing was deleted.{folders_note}"
            messagebox.showinfo("Duplicate Finder", message)

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
