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
from tkinter import Listbox, Menu, messagebox, ttk
from typing import Callable, Optional

import customtkinter as ctk

from src.config.app_info import HELP_RESULTS
from src.config.settings import Settings
from src.core.deleter import DeleteProgress, DeleteResult, delete_to_recycle_bin, remove_empty_folders
from src.core.models import DuplicateGroup, FileEntry, ScanResult
from src.ui.about_window import show_about
from src.ui.delete_progress_window import DeleteProgressWindow
from src.ui.info_dialog import show_info_dialog
from src.utils.formatters import format_count

logger = logging.getLogger(__name__)

FILE_FONT_SIZE = 14
CHECK_ON = "☑"
CHECK_OFF = "☐"
COL_CHECK = "check"
COL_NAME = "name"
COL_SIZE = "size"
COL_PATH = "path"


def _format_size(num_bytes: int) -> str:
    """Отформатировать размер файла для таблицы."""
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
    """Заголовок группы дубликатов в списке."""
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
        settings: Settings,
        on_back: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        """Создать страницу результатов с таблицей дубликатов и удалением."""
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.on_back = on_back
        self.on_cancel = on_cancel
        self._result: ScanResult | None = None
        self._selected_group_index: int = -1
        self._entry_by_path: dict[Path, FileEntry] = {}
        self._checked_paths: set[Path] = set()
        self._sort_column: str | None = None
        self._sort_reverse = False
        self._delete_mode = ctk.StringVar(value="custom")
        self._clean_empty_folders = ctk.BooleanVar(value=bool(settings.clean_empty_folders))
        self._delete_queue: queue.Queue = queue.Queue()
        self._delete_thread: threading.Thread | None = None
        self._delete_cancel = threading.Event()
        self._delete_progress: DeleteProgressWindow | None = None

        self._create_widgets()
        self.after(100, self._process_delete_queue)

    def _create_widgets(self) -> None:
        """Создать виджеты страницы результатов."""
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
                "or right-click for more options, including Rename. "
                "Click a column header to sort."
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
            command=self._on_clean_empty_changed,
        ).pack(anchor="w", padx=10, pady=(0, 6))

        # По умолчанию скрыт — показывается только в two_lists
        self.delete_mode_frame.pack_forget()

        table_frame = ctk.CTkFrame(content)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tree_host = ctk.CTkFrame(table_frame, fg_color="#1a1a1a")
        tree_host.pack(fill="both", expand=True, padx=4, pady=4)

        self._configure_tree_style()
        self.files_tree = ttk.Treeview(
            tree_host,
            columns=(COL_CHECK, COL_NAME, COL_SIZE, COL_PATH),
            show="headings",
            selectmode="browse",
            style="Results.Treeview",
        )
        self.files_tree.heading(
            COL_CHECK,
            text="",
            command=lambda: self._sort_by(COL_CHECK),
        )
        self.files_tree.heading(
            COL_NAME,
            text="Filename",
            command=lambda: self._sort_by(COL_NAME),
            anchor="w",
        )
        self.files_tree.heading(
            COL_SIZE,
            text="File Size",
            command=lambda: self._sort_by(COL_SIZE),
            anchor="w",
        )
        self.files_tree.heading(
            COL_PATH,
            text="Original Path",
            command=lambda: self._sort_by(COL_PATH),
            anchor="w",
        )
        self.files_tree.column(COL_CHECK, width=36, minwidth=36, stretch=False, anchor="center")
        self.files_tree.column(COL_NAME, width=220, minwidth=80, stretch=False, anchor="w")
        self.files_tree.column(COL_SIZE, width=110, minwidth=70, stretch=False, anchor="w")
        self.files_tree.column(COL_PATH, width=420, minwidth=120, stretch=True, anchor="w")

        y_scroll = ttk.Scrollbar(tree_host, orient="vertical", command=self.files_tree.yview)
        x_scroll = ttk.Scrollbar(tree_host, orient="horizontal", command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.files_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        tree_host.grid_rowconfigure(0, weight=1)
        tree_host.grid_columnconfigure(0, weight=1)

        self.files_tree.bind("<Button-1>", self._on_tree_click)
        self.files_tree.bind("<Button-3>", self._on_tree_right_click)
        self.files_tree.bind("<space>", self._on_tree_space)

    def _configure_tree_style(self) -> None:
        """Настроить стиль Treeview под тёмную тему."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:  # noqa: BLE001
            pass
        style.configure(
            "Results.Treeview",
            background="#1a1a1a",
            foreground="#e8e8e8",
            fieldbackground="#1a1a1a",
            borderwidth=0,
            rowheight=28,
            font=("Segoe UI", FILE_FONT_SIZE),
        )
        style.configure(
            "Results.Treeview.Heading",
            background="#2b2b2b",
            foreground="#e8e8e8",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", FILE_FONT_SIZE, "bold"),
        )
        style.map(
            "Results.Treeview",
            background=[("selected", "#3a3a3a")],
            foreground=[("selected", "#ffffff")],
        )
        style.map(
            "Results.Treeview.Heading",
            background=[("active", "#3a3a3a")],
        )

    def save_to_settings(self) -> None:
        """Сохранить состояние чекбокса очистки пустых папок."""
        self.settings.clean_empty_folders = bool(self._clean_empty_folders.get())

    def _on_clean_empty_changed(self) -> None:
        """Сохранить флаг очистки пустых папок в settings."""
        self.save_to_settings()

    def show_results(self, result: ScanResult) -> None:
        """Отобразить результаты сканирования."""
        self._clean_empty_folders.set(bool(self.settings.clean_empty_folders))
        self._result = result
        self._selected_group_index = -1
        self._entry_by_path.clear()
        self._checked_paths.clear()
        self._sort_column = None
        self._sort_reverse = False
        self._clear_table()
        self.sets_list.delete(0, "end")
        self._delete_mode.set("custom")
        self._update_heading_labels()

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

    def _on_set_selected(self, _event: object = None) -> None:
        """Переключить режим выбора файлов для удаления."""
        selection = self.sets_list.curselection()
        if not selection:
            return
        self._show_group(int(selection[0]))

    def _show_group(self, index: int) -> None:
        """Показать файлы выбранной группы дубликатов."""
        if not self._result or index < 0 or index >= len(self._result.groups):
            return
        self._selected_group_index = index
        self._render_table(self._result.groups[index])

    def _clear_table(self) -> None:
        """Очистить таблицу файлов текущей группы."""
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

    def _path_from_iid(self, iid: str) -> Path:
        """Преобразовать iid строки Treeview в Path."""
        return Path(iid)

    def _render_table(self, group: DuplicateGroup) -> None:
        """Заполнить таблицу файлами выбранной группы."""
        self._clear_table()
        self._entry_by_path.clear()

        for entry in group.files:
            self._entry_by_path[entry.path] = entry
            check = CHECK_ON if entry.path in self._checked_paths else CHECK_OFF
            self.files_tree.insert(
                "",
                "end",
                iid=str(entry.path),
                values=(
                    check,
                    entry.path.name,
                    _format_size(entry.size),
                    str(entry.path),
                ),
            )

        if self._sort_column:
            self._apply_sort(self._sort_column, reverse=self._sort_reverse, update_heading=False)

    def _heading_title(self, column: str) -> str:
        """Текст заголовка колонки с индикатором сортировки."""
        titles = {
            COL_CHECK: "",
            COL_NAME: "Filename",
            COL_SIZE: "File Size",
            COL_PATH: "Original Path",
        }
        title = titles.get(column, column)
        if self._sort_column != column:
            return title
        return f"{title} {'▼' if self._sort_reverse else '▲'}".strip()

    def _update_heading_labels(self) -> None:
        """Обновить подписи заголовков колонок."""
        for column in (COL_CHECK, COL_NAME, COL_SIZE, COL_PATH):
            self.files_tree.heading(column, text=self._heading_title(column))

    def _sort_by(self, column: str) -> None:
        """Переключить сортировку по колонке."""
        reverse = self._sort_column == column and not self._sort_reverse
        self._apply_sort(column, reverse=reverse, update_heading=True)

    def _apply_sort(self, column: str, *, reverse: bool, update_heading: bool) -> None:
        """Применить сортировку строк таблицы."""
        items = list(self.files_tree.get_children(""))
        if not items:
            return

        def sort_key(iid: str) -> object:
            """Ключ сортировки для iid строки таблицы."""
            path = self._path_from_iid(iid)
            entry = self._entry_by_path.get(path)
            if column == COL_CHECK:
                return 0 if path in self._checked_paths else 1
            if column == COL_NAME:
                return path.name.lower()
            if column == COL_SIZE:
                return entry.size if entry else 0
            return str(path).lower()

        items.sort(key=sort_key, reverse=reverse)
        for index, iid in enumerate(items):
            self.files_tree.move(iid, "", index)

        self._sort_column = column
        self._sort_reverse = reverse
        if update_heading:
            self._update_heading_labels()

    def _on_tree_click(self, event: object) -> str | None:
        """Обработать клик по строке/чекбоксу таблицы."""
        tree = self.files_tree
        region = tree.identify_region(event.x, event.y)  # type: ignore[attr-defined]
        if region != "cell":
            return None
        column = tree.identify_column(event.x)  # type: ignore[attr-defined]
        row = tree.identify_row(event.y)  # type: ignore[attr-defined]
        if not row:
            return None
        # #1 = check column
        if column == "#1":
            path = self._path_from_iid(row)
            self._set_checked(path, path not in self._checked_paths)
            return "break"
        return None

    def _on_tree_space(self, _event: object) -> str:
        """Переключить чекбокс выделенной строки по Space."""
        selection = self.files_tree.selection()
        if selection:
            path = self._path_from_iid(selection[0])
            self._set_checked(path, path not in self._checked_paths)
        return "break"

    def _on_tree_right_click(self, event: object) -> None:
        """Показать контекстное меню по правому клику."""
        row = self.files_tree.identify_row(event.y)  # type: ignore[attr-defined]
        if not row:
            return
        self.files_tree.selection_set(row)
        self._show_context_menu(event, self._path_from_iid(row))

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
        """Синхронизировать чекбоксы с _checked_paths."""
        for iid in self.files_tree.get_children(""):
            path = self._path_from_iid(iid)
            values = list(self.files_tree.item(iid, "values"))
            if not values:
                continue
            values[0] = CHECK_ON if path in self._checked_paths else CHECK_OFF
            self.files_tree.item(iid, values=values)

    def _show_context_menu(self, event: object, path: Path) -> None:
        """Показать контекстное меню для файла в таблице."""
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
        """Установить или снять выбор файла."""
        if value:
            self._checked_paths.add(path)
        else:
            self._checked_paths.discard(path)
        iid = str(path)
        if self.files_tree.exists(iid):
            values = list(self.files_tree.item(iid, "values"))
            if values:
                values[0] = CHECK_ON if value else CHECK_OFF
                self.files_tree.item(iid, values=values)

    def _open_folder(self, path: Path) -> None:
        """Открыть папку файла в проводнике ОС."""
        folder = path.parent
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
        """Переименовать файл через диалог ввода имени."""
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
        return sorted(self._checked_paths, key=lambda p: str(p).lower())

    def _handle_next(self) -> None:
        """Запустить удаление выбранных дубликатов."""
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
        """Запустить фоновое удаление с окном прогресса."""
        self._delete_cancel.clear()
        self.next_btn.configure(state="disabled")
        self.back_btn.configure(state="disabled")

        self._delete_progress = DeleteProgressWindow(
            self.winfo_toplevel(),
            total=max(len(selected), 1),
            on_cancel=self._delete_cancel.set,
            initial_phase="folders" if (clean_empty and not selected) else "files",
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
        """Воркер удаления файлов и пустых папок."""
        try:
            def progress_callback(progress: DeleteProgress) -> None:
                """Поставить прогресс удаления в очередь UI."""
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
                    progress_callback=progress_callback,
                    cancel_check=self._delete_cancel.is_set,
                )
                result.folders_removed = folders_removed
                result.folders_failed = folders_failed
                if self._delete_cancel.is_set():
                    result.canceled = True
            self._delete_queue.put(("done", result))
        except Exception as exc:
            logger.exception("Delete failed")
            self._delete_queue.put(("error", str(exc)))

    def _process_delete_queue(self) -> None:
        """Обработать сообщения из очереди удаления на UI-потоке."""
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
        """Закрыть окно прогресса удаления."""
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
        """Обработать завершение удаления на UI-потоке."""
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
        """Показать ошибку удаления на UI-потоке."""
        self._close_delete_progress()
        messagebox.showerror("Delete error", message)

    def _remove_deleted_files(self, deleted: set[Path]) -> None:
        """Убрать удалённые файлы из результата и таблицы."""
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
        """Вернуться на страницу настройки поиска."""
        if self.on_back:
            self.on_back()

    def _handle_cancel(self) -> None:
        """Закрыть приложение со страницы результатов."""
        if self.on_cancel:
            self.on_cancel()

    def _show_about(self) -> None:
        """Открыть окно About."""
        show_about(self)

    def _show_results_help(self) -> None:
        """Показать справку по экрану результатов."""
        show_info_dialog(self, "Results", HELP_RESULTS, width=520)
