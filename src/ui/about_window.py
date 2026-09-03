"""
Окно «О программе» / справка.
"""

from __future__ import annotations

import webbrowser

import customtkinter as ctk

from src.config.app_info import (
    APP_COPYRIGHT_HOLDER,
    APP_COPYRIGHT_RANGE,
    APP_DESCRIPTION,
    APP_DEVELOPER,
    APP_LICENSE_NAME,
    APP_NAME,
    APP_OSS_LABEL,
    APP_OSS_URL,
    APP_VERSION,
    APP_WEBSITE,
    HELP_RESULTS,
    HELP_SEARCH,
    HELP_TWO_LISTS,
)

_LINK_COLOR = "#6cb6ff"
_MUTED_COLOR = "gray75"


class AboutWindow(ctk.CTkToplevel):
    """Полноценное окно информации о программе."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkToplevel | ctk.CTkFrame,
        help_topic: str = "general",
    ):
        root = parent.winfo_toplevel()
        super().__init__(root)
        self.title(f"About {APP_NAME}")
        self.geometry("560x520")
        self.minsize(520, 440)
        self.resizable(True, True)

        self.transient(root)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        footer = ctk.CTkFrame(self, fg_color="transparent", height=48)
        footer.pack(side="bottom", fill="x", padx=16, pady=(0, 12))
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="Close",
            width=100,
            command=self.destroy,
        ).pack(side="right")

        body = ctk.CTkScrollableFrame(self)
        body.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        ctk.CTkLabel(
            body,
            text=APP_NAME,
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 2))

        ctk.CTkLabel(
            body,
            text=f"Version {APP_VERSION}",
            anchor="w",
            text_color=_MUTED_COLOR,
        ).pack(fill="x", pady=(0, 12))

        self._section_title(body, "Description")
        ctk.CTkLabel(
            body,
            text=APP_DESCRIPTION,
            anchor="w",
            justify="left",
            wraplength=500,
        ).pack(fill="x", pady=(0, 12))

        self._section_title(body, "Help")
        help_text = self._help_for_topic(help_topic)
        ctk.CTkLabel(
            body,
            text=help_text,
            anchor="w",
            justify="left",
            wraplength=500,
        ).pack(fill="x", pady=(0, 12))

        self._section_title(body, "Developer")
        ctk.CTkLabel(
            body,
            text=APP_DEVELOPER,
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        self._section_title(body, "Project website")
        ctk.CTkLabel(
            body,
            text="More projects and contacts:",
            anchor="w",
        ).pack(fill="x", pady=(0, 2))
        self._link_label(body, APP_WEBSITE, APP_WEBSITE).pack(anchor="w", pady=(0, 12))

        self._section_title(body, "License agreement")
        ctk.CTkLabel(
            body,
            text=APP_LICENSE_NAME,
            anchor="w",
            text_color=_MUTED_COLOR,
        ).pack(fill="x", pady=(0, 16))

        powered_row = ctk.CTkFrame(body, fg_color="transparent")
        powered_row.pack(fill="x", pady=(4, 2))
        ctk.CTkLabel(
            powered_row,
            text="Powered by ",
            anchor="w",
            text_color=_MUTED_COLOR,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self._link_label(
            powered_row,
            APP_OSS_LABEL,
            APP_OSS_URL,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")

        copyright_row = ctk.CTkFrame(body, fg_color="transparent")
        copyright_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            copyright_row,
            text=f"Copyright © {APP_COPYRIGHT_RANGE} ",
            anchor="w",
            text_color=_MUTED_COLOR,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self._link_label(
            copyright_row,
            APP_COPYRIGHT_HOLDER,
            APP_WEBSITE,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")

        self.after(50, self._activate_modal)

    def _section_title(self, parent: ctk.CTkBaseClass, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 4))

    def _link_label(
        self,
        parent: ctk.CTkBaseClass,
        text: str,
        url: str,
        font: ctk.CTkFont | None = None,
    ) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            parent,
            text=text,
            anchor="w",
            text_color=_LINK_COLOR,
            cursor="hand2",
            font=font,
        )
        label.bind("<Button-1>", lambda _event: webbrowser.open(url))
        return label

    def _help_for_topic(self, topic: str) -> str:
        if topic == "two_lists":
            return HELP_TWO_LISTS
        if topic == "results":
            return HELP_RESULTS
        return HELP_SEARCH

    def _activate_modal(self) -> None:
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:  # noqa: BLE001
            pass


def show_about(
    parent: ctk.CTk | ctk.CTkToplevel | ctk.CTkFrame,
    help_topic: str = "general",
) -> AboutWindow:
    """Открыть окно About (одно на родителя)."""
    window = AboutWindow(parent, help_topic=help_topic)
    return window
