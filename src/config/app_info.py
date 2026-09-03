"""Метаданные приложения для UI и сборки."""

from __future__ import annotations

APP_NAME = "Duplicate Finder"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = (
    "Desktop application for finding and removing duplicate files. "
    "Compare one list of paths or two lists against each other, "
    "match by exact file content or by filename, optionally limit "
    "the search to images, then move unwanted copies to the Recycle Bin."
)
APP_DEVELOPER = "Denis Peshkov"
APP_WEBSITE = "https://peshkov.biz"
APP_WEBSITE_LABEL = "peshkov.biz"
APP_LICENSE_NAME = "MIT License"

APP_LICENSE_TEXT = """\
MIT License

Copyright (c) 2026 Denis Peshkov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

HELP_SEARCH = (
    "Single list: find duplicates within one set of paths.\n"
    "Two lists: compare files between two sets.\n"
    "Exact duplicate: compare file content by hash.\n"
    "Same filename: compare file names only.\n"
    "Deleted files are moved to the Recycle Bin."
)

HELP_TWO_LISTS = (
    "Two-list mode finds duplicates between File List 1 and File List 2.\n"
    "Files from List 1 are matched against files in List 2."
)

HELP_RESULTS = (
    "Top list shows duplicate sets.\n"
    "Select a set to see files in the table.\n"
    "Two-list modes:\n"
    "  Custom — clear all marks, then select manually.\n"
    "  Delete from File List 1/2 — clear all, mark that list.\n"
    "Press Next to move selected files to Recycle Bin.\n"
    "Right-click a file for Rename / Open folder."
)
