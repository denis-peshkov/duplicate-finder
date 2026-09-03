"""Простые информационные диалоги с задаваемой шириной."""

from __future__ import annotations

import customtkinter as ctk


def show_info_dialog(
    parent: ctk.CTk | ctk.CTkToplevel | ctk.CTkFrame,
    title: str,
    message: str,
    *,
    width: int = 400,
) -> None:
    """Показать модальное окно с текстом справки (шире системного messagebox)."""
    root = parent.winfo_toplevel()
    dialog = ctk.CTkToplevel(root)
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.transient(root)

    frame = ctk.CTkFrame(dialog, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=20, pady=16)

    ctk.CTkLabel(
        frame,
        text=message,
        anchor="w",
        justify="left",
        wraplength=width - 48,
    ).pack(fill="x", pady=(0, 16))

    ctk.CTkButton(
        frame,
        text="OK",
        width=90,
        command=dialog.destroy,
    ).pack(anchor="e")

    dialog.update_idletasks()
    needed_h = max(frame.winfo_reqheight() + 32, 140)
    dialog.geometry(f"{width}x{needed_h}")

    dialog.lift()
    dialog.focus_force()
    dialog.grab_set()
    dialog.wait_window()
