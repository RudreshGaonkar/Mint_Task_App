"""Theme module for Mint Tasks — Modern Visual System.

Implements Material Design 3 inspired styling: vertical sidebar navigation,
floating cards with soft elevation, Mint Green accent palette,
smooth fade transitions, and modern typography hierarchy.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from database import ensure_secure_dir, ensure_secure_file, get_xdg_config_dir


def get_config_file_path() -> Path:
    return get_xdg_config_dir() / "config.json"


def load_config() -> Dict[str, Any]:
    config_file = get_config_file_path()
    default_config = {
        "theme": "dark",
        "sound_alerts": True,
        "minimize_to_tray": True,
        "window_width": 960,
        "window_height": 680,
    }
    if not config_file.exists():
        save_config(default_config)
        return default_config
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            default_config.update(data)
            return default_config
    except Exception:
        return default_config


def save_config(config: Dict[str, Any]) -> None:
    config_dir = get_xdg_config_dir()
    config_file = get_config_file_path()
    ensure_secure_dir(config_dir)
    ensure_secure_file(config_file)
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        os.chmod(config_file, 0o600)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Color Palettes
# ---------------------------------------------------------------------------

class DarkPalette:
    PRIMARY          = "#82E0AA"   # Desaturated Mint Green
    PRIMARY_CONTAINER= "#1B4F37"   # Deep accent bg for active items
    BG               = "#1E1F22"   # True dark gray background
    SURFACE          = "#2B2D31"   # Elevated cards / components
    SURFACE_VAR      = "#313338"   # Input fields / secondary bg
    SURFACE_HOVER    = "#36383F"
    SURFACE_ACTIVE   = "#404249"
    TEXT             = "#E3E5E8"   # Soft near-white
    TEXT_SECONDARY   = "#A9ABB0"   # Muted subtitle
    BORDER           = "#3A3C42"
    STAR             = "#F9E2AF"
    DANGER           = "#F28B82"
    SUCCESS          = "#82E0AA"
    WARNING          = "#F9E2AF"
    SHADOW_COLOR     = "rgba(0,0,0,0.4)"


class LightPalette:
    PRIMARY          = "#00C853"   # Vibrant Mint Green
    PRIMARY_CONTAINER= "#E0F7EB"   # Soft accent bg for active items
    BG               = "#F8F9FA"   # Clean light gray background
    SURFACE          = "#FFFFFF"   # Main cards / component backgrounds
    SURFACE_VAR      = "#F1F3F4"   # Input fields / secondary bg
    SURFACE_HOVER    = "#E8F0FE"
    SURFACE_ACTIVE   = "#D2E3FC"
    TEXT             = "#212121"   # High contrast charcoal
    TEXT_SECONDARY   = "#5F6368"   # Muted subtitle
    BORDER           = "#E0E0E0"
    STAR             = "#F59F00"
    DANGER           = "#D93025"
    SUCCESS          = "#00C853"
    WARNING          = "#F59F00"
    SHADOW_COLOR     = "rgba(0,0,0,0.13)"


def get_stylesheet(theme: str = "dark") -> str:
    """Generate the full Material Design 3-inspired QSS stylesheet."""
    D = DarkPalette if theme == "dark" else LightPalette

    # Typography: system UI font stack with Noto Sans as a known-available fallback
    FONT_UI = '"Noto Sans", "Segoe UI", Roboto, Ubuntu, Cantarell, sans-serif'
    FONT_MONO = '"Noto Sans Mono", "Cascadia Code", "Consolas", monospace'

    return f"""
/* ===================================================================
   GLOBAL RESETS & BASE
=================================================================== */
QWidget {{
    font-family: {FONT_UI};
    font-size: 13px;
    color: {D.TEXT};
    background-color: transparent;
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {D.BG};
}}

/* ===================================================================
   SIDEBAR NAVIGATION
=================================================================== */
QWidget#sidebarWidget {{
    background-color: {D.SURFACE};
    border-right: 1px solid {D.BORDER};
    min-width: 200px;
    max-width: 220px;
}}

QLabel#appLogoLabel {{
    font-size: 18px;
    font-weight: 700;
    color: {D.PRIMARY};
    padding: 18px 16px 10px 16px;
    letter-spacing: 0.4px;
}}

QPushButton.navButton {{
    background-color: transparent;
    color: {D.TEXT_SECONDARY};
    border: none;
    border-radius: 10px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    margin: 2px 8px;
}}

QPushButton.navButton:hover {{
    background-color: {D.SURFACE_HOVER};
    color: {D.TEXT};
}}

QPushButton.navButton[active="true"] {{
    background-color: {D.PRIMARY_CONTAINER};
    color: {D.PRIMARY};
    font-weight: 600;
}}

/* Sidebar bottom buttons */
QPushButton#themeToggleBtn {{
    background-color: transparent;
    color: {D.TEXT_SECONDARY};
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    text-align: left;
    font-size: 12px;
    margin: 2px 8px;
}}

QPushButton#themeToggleBtn:hover {{
    background-color: {D.SURFACE_HOVER};
    color: {D.TEXT};
}}

/* ===================================================================
   CONTENT AREA
=================================================================== */
QWidget#contentStack {{
    background-color: {D.BG};
}}

QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

/* ===================================================================
   TASK CARDS — FLOATING ELEVATION
=================================================================== */
QFrame#taskCard {{
    background-color: {D.SURFACE};
    border-radius: 12px;
    border: none;
    margin: 4px 12px;
    padding: 2px;
}}

QFrame#taskCard:hover {{
    background-color: {D.SURFACE_HOVER};
}}

QFrame#subtaskCard {{
    background-color: {D.SURFACE_VAR};
    border-radius: 8px;
    border: none;
    margin: 3px 0 3px 24px;
}}

QFrame#subtaskCard:hover {{
    background-color: {D.SURFACE_HOVER};
}}

/* ===================================================================
   TASK QUICK-ADD BAR
=================================================================== */
QFrame#addTaskBar {{
    background-color: {D.SURFACE};
    border-radius: 12px;
    border: none;
    margin: 8px 12px 4px 12px;
    padding: 4px;
}}

/* ===================================================================
   BUTTONS
=================================================================== */
/* Contained (Primary) Button */
QPushButton#primaryBtn {{
    background-color: {D.PRIMARY};
    color: {"#101212" if theme == "dark" else "#FFFFFF"};
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton#primaryBtn:hover {{
    background-color: {"#96E8B8" if theme == "dark" else "#00E676"};
}}

QPushButton#primaryBtn:pressed {{
    background-color: {"#6DCFA0" if theme == "dark" else "#00BF4A"};
}}

/* Outlined Button */
QPushButton {{
    background-color: transparent;
    color: {D.TEXT};
    border: 1px solid {D.BORDER};
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {D.SURFACE_HOVER};
    border-color: {D.PRIMARY};
    color: {D.PRIMARY};
}}

QPushButton:pressed {{
    background-color: {D.SURFACE_ACTIVE};
}}

/* Icon-only ghost buttons */
QPushButton#iconBtn {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 4px 6px;
    font-size: 15px;
    color: {D.TEXT_SECONDARY};
}}

QPushButton#iconBtn:hover {{
    background-color: {D.SURFACE_HOVER};
    color: {D.TEXT};
}}

/* Star Button */
QPushButton#starBtn {{
    background-color: transparent;
    border: none;
    padding: 3px;
    font-size: 17px;
    color: {D.TEXT_SECONDARY};
    border-radius: 5px;
}}

QPushButton#starBtn[starred="true"] {{
    color: {D.STAR};
}}

QPushButton#starBtn:hover {{
    background-color: {D.SURFACE_HOVER};
}}

/* Danger / destructive */
QPushButton#dangerBtn {{
    background-color: transparent;
    color: {D.DANGER};
    border: 1px solid {D.DANGER};
    border-radius: 8px;
    padding: 6px 14px;
}}

QPushButton#dangerBtn:hover {{
    background-color: {D.DANGER};
    color: {"#101212" if theme == "dark" else "#FFFFFF"};
}}

/* ===================================================================
   INPUTS & TEXT FIELDS
=================================================================== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {D.SURFACE_VAR};
    color: {D.TEXT};
    border: none;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 13px;
    selection-background-color: {D.PRIMARY};
    selection-color: {"#101212" if theme == "dark" else "#FFFFFF"};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-bottom: 2px solid {D.PRIMARY};
    border-radius: 6px 6px 0 0;
}}

QPlainTextEdit {{
    font-family: {FONT_MONO};
    font-size: 12px;
    line-height: 1.5;
}}

/* Date and Time Pickers */
QDateEdit, QTimeEdit, QDateTimeEdit {{
    background-color: {D.SURFACE_VAR};
    color: {D.TEXT};
    border: 1px solid {D.BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 20px;
}}

QDateEdit:focus, QTimeEdit:focus {{
    border-color: {D.PRIMARY};
}}

QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {D.BORDER};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}

QDateEdit::drop-down:hover, QTimeEdit::drop-down:hover {{
    background-color: {D.SURFACE_HOVER};
}}

QCalendarWidget {{
    background-color: {D.SURFACE};
    color: {D.TEXT};
    border: 1px solid {D.BORDER};
    border-radius: 8px;
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {D.SURFACE_VAR};
    padding: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}}

QCalendarWidget QAbstractItemView:enabled {{
    background-color: {D.SURFACE};
    color: {D.TEXT};
    selection-background-color: {D.PRIMARY};
    selection-color: {"#101212" if theme == "dark" else "#FFFFFF"};
}}

QCalendarWidget QToolButton {{
    background-color: transparent;
    color: {D.TEXT};
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: bold;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {D.SURFACE_HOVER};
}}

QCalendarWidget QMenu {{
    width: 120px;
    left: 20px;
    color: {D.TEXT};
    background-color: {D.SURFACE};
}}

QCalendarWidget QSpinBox {{
    width: 50px;
    font-size: 13px;
    color: {D.TEXT};
    background-color: {D.SURFACE_VAR};
    selection-background-color: {D.PRIMARY};
    selection-color: {"#101212" if theme == "dark" else "#FFFFFF"};
}}

/* ===================================================================
   CHECKBOXES
=================================================================== */
QCheckBox {{
    spacing: 8px;
    color: {D.TEXT};
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 10px;
    border: 2px solid {D.BORDER};
    background-color: transparent;
}}

QCheckBox::indicator:hover {{
    border-color: {D.PRIMARY};
    background-color: {D.SURFACE_HOVER};
}}

QCheckBox::indicator:checked {{
    background-color: {D.PRIMARY};
    border-color: {D.PRIMARY};
}}

/* ===================================================================
   SCROLLBARS — Ultra-Minimal
=================================================================== */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
    border-radius: 3px;
}}

QScrollBar::handle:vertical {{
    background: {D.BORDER};
    border-radius: 3px;
    min-height: 32px;
}}

QScrollBar::handle:vertical:hover {{
    background: {D.TEXT_SECONDARY};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal {{
    background: {D.BORDER};
    border-radius: 3px;
    min-width: 32px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ===================================================================
   NOTES MULTI-TAB
=================================================================== */
QTabWidget#notesTabWidget::pane {{
    background: {D.BG};
    border: none;
}}

QTabBar#notesTabBar::tab {{
    background: transparent;
    color: {D.TEXT_SECONDARY};
    padding: 7px 16px;
    border-radius: 8px 8px 0 0;
    margin-right: 2px;
    font-size: 12px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
}}

QTabBar#notesTabBar::tab:hover {{
    color: {D.TEXT};
    background: {D.SURFACE_HOVER};
}}

QTabBar#notesTabBar::tab:selected {{
    color: {D.PRIMARY};
    background: {D.PRIMARY_CONTAINER};
    border-bottom: 2px solid {D.PRIMARY};
    font-weight: 600;
}}

/* ===================================================================
   BADGES & LABELS
=================================================================== */
QLabel#badgeOverdue {{
    background-color: {D.DANGER};
    color: {"#101212" if theme == "dark" else "#FFFFFF"};
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}}

QLabel#badgeToday {{
    background-color: {D.WARNING};
    color: #101212;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}}

QLabel#badgeUpcoming {{
    background-color: {D.SURFACE_VAR};
    color: {D.TEXT_SECONDARY};
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
}}

QLabel#mutedLabel {{
    color: {D.TEXT_SECONDARY};
    font-size: 11px;
}}

QLabel#sectionHeader {{
    color: {D.TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

QLabel#taskTitle {{
    color: {D.TEXT};
    font-size: 13px;
    font-weight: 500;
}}

QLabel#taskTitleDone {{
    color: {D.TEXT_SECONDARY};
    font-size: 13px;
    font-weight: 400;
}}

/* ===================================================================
   STATUS BAR (Notes)
=================================================================== */
QLabel#statusLabel {{
    color: {D.TEXT_SECONDARY};
    font-size: 11px;
    padding: 2px 6px;
}}

QFrame#statusBar {{
    background-color: {D.SURFACE};
    border-top: 1px solid {D.BORDER};
}}

/* ===================================================================
   DIALOGS & MENUS
=================================================================== */
QDialog {{
    background-color: {D.SURFACE};
    border-radius: 12px;
}}

QMessageBox {{
    background-color: {D.SURFACE};
}}

QMenu {{
    background-color: {D.SURFACE};
    color: {D.TEXT};
    border: 1px solid {D.BORDER};
    border-radius: 10px;
    padding: 6px 4px;
}}

QMenu::item {{
    padding: 7px 24px 7px 14px;
    border-radius: 6px;
    margin: 1px 4px;
}}

QMenu::item:selected {{
    background-color: {D.PRIMARY_CONTAINER};
    color: {D.PRIMARY};
}}

QMenu::separator {{
    height: 1px;
    background-color: {D.BORDER};
    margin: 4px 10px;
}}

/* ===================================================================
   SEPARATOR LINES
=================================================================== */
QFrame#hSeparator {{
    background-color: {D.BORDER};
    max-height: 1px;
    border: none;
}}

QFrame#vSeparator {{
    background-color: {D.BORDER};
    max-width: 1px;
    border: none;
}}

/* ===================================================================
   DIALOG BUTTON BOX
=================================================================== */
QDialogButtonBox QPushButton {{
    min-width: 80px;
}}
"""
