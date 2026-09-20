"""Theme and styling module for Mint Tasks.

Provides custom QSS stylesheets for Dark and Light modes adhering to Google Tasks
minimalist aesthetics, along with XDG-compliant configuration persistence.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict
from database import ensure_secure_dir, ensure_secure_file, get_xdg_config_dir


def get_config_file_path() -> Path:
    """Return path to config.json in XDG Config Directory."""
    return get_xdg_config_dir() / "config.json"


def load_config() -> Dict[str, Any]:
    """Load user preferences from config.json."""
    config_file = get_config_file_path()
    default_config = {
        "theme": "dark",
        "sound_alerts": True,
        "minimize_to_tray": True,
        "window_width": 850,
        "window_height": 650,
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
    """Save user preferences to config.json securely."""
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


class ColorPalette:
    """Color token constants for Dark and Light themes."""

    # Dark Mode (Catppuccin/Google Tasks hybrid dark)
    DARK_BG = "#1e1e2e"
    DARK_SURFACE = "#2a2b3d"
    DARK_SURFACE_HOVER = "#36384f"
    DARK_SURFACE_ACTIVE = "#3e405a"
    DARK_TEXT = "#cdd6f4"
    DARK_TEXT_MUTED = "#a6adc8"
    DARK_BORDER = "#313244"
    DARK_ACCENT = "#89b4fa"
    DARK_ACCENT_HOVER = "#b4befe"
    DARK_DANGER = "#f38ba8"
    DARK_SUCCESS = "#a6e3a1"
    DARK_WARNING = "#f9e2af"
    DARK_STAR = "#f9e2af"

    # Light Mode (Clean Google Tasks light)
    LIGHT_BG = "#f8f9fa"
    LIGHT_SURFACE = "#ffffff"
    LIGHT_SURFACE_HOVER = "#f1f3f5"
    LIGHT_SURFACE_ACTIVE = "#e9ecef"
    LIGHT_TEXT = "#212529"
    LIGHT_TEXT_MUTED = "#6c757d"
    LIGHT_BORDER = "#dee2e6"
    LIGHT_ACCENT = "#0d6efd"
    LIGHT_ACCENT_HOVER = "#0b5ed7"
    LIGHT_DANGER = "#dc3545"
    LIGHT_SUCCESS = "#198754"
    LIGHT_WARNING = "#fd7e14"
    LIGHT_STAR = "#f59f00"


def get_stylesheet(theme: str = "dark") -> str:
    """Generate complete application stylesheet for the given theme."""
    is_dark = theme.lower() == "dark"

    bg = ColorPalette.DARK_BG if is_dark else ColorPalette.LIGHT_BG
    surface = ColorPalette.DARK_SURFACE if is_dark else ColorPalette.LIGHT_SURFACE
    surface_hover = ColorPalette.DARK_SURFACE_HOVER if is_dark else ColorPalette.LIGHT_SURFACE_HOVER
    surface_active = ColorPalette.DARK_SURFACE_ACTIVE if is_dark else ColorPalette.LIGHT_SURFACE_ACTIVE
    text = ColorPalette.DARK_TEXT if is_dark else ColorPalette.LIGHT_TEXT
    text_muted = ColorPalette.DARK_TEXT_MUTED if is_dark else ColorPalette.LIGHT_TEXT_MUTED
    border = ColorPalette.DARK_BORDER if is_dark else ColorPalette.LIGHT_BORDER
    accent = ColorPalette.DARK_ACCENT if is_dark else ColorPalette.LIGHT_ACCENT
    accent_hover = ColorPalette.DARK_ACCENT_HOVER if is_dark else ColorPalette.LIGHT_ACCENT_HOVER
    danger = ColorPalette.DARK_DANGER if is_dark else ColorPalette.LIGHT_DANGER
    success = ColorPalette.DARK_SUCCESS if is_dark else ColorPalette.LIGHT_SUCCESS
    warning = ColorPalette.DARK_WARNING if is_dark else ColorPalette.LIGHT_WARNING
    star_color = ColorPalette.DARK_STAR if is_dark else ColorPalette.LIGHT_STAR

    return f"""
    /* Global Application Styles */
    QMainWindow, QWidget#centralWidget {{
        background-color: {bg};
        color: {text};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
        font-size: 13px;
    }}

    QWidget {{
        color: {text};
    }}

    /* Header Bar */
    QFrame#headerFrame {{
        background-color: {surface};
        border-bottom: 1px solid {border};
        padding: 6px 12px;
    }}

    QLabel#appTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {accent};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {surface_hover};
        border-color: {accent};
    }}

    QPushButton:pressed {{
        background-color: {surface_active};
    }}

    QPushButton#accentButton {{
        background-color: {accent};
        color: {("#11111b" if is_dark else "#ffffff")};
        border: none;
        font-weight: 600;
    }}

    QPushButton#accentButton:hover {{
        background-color: {accent_hover};
    }}

    QPushButton#dangerButton {{
        background-color: transparent;
        color: {danger};
        border: 1px solid {danger};
    }}

    QPushButton#dangerButton:hover {{
        background-color: {danger};
        color: #ffffff;
    }}

    QPushButton#iconButton {{
        background-color: transparent;
        border: none;
        padding: 4px;
        border-radius: 4px;
    }}

    QPushButton#iconButton:hover {{
        background-color: {surface_hover};
    }}

    QPushButton#starButton {{
        background-color: transparent;
        border: none;
        font-size: 16px;
        color: {text_muted};
    }}

    QPushButton#starButton[starred="true"] {{
        color: {star_color};
    }}

    /* Navigation Tabs */
    QTabWidget::pane {{
        border: none;
        background: {bg};
    }}

    QTabBar::tab {{
        background: transparent;
        color: {text_muted};
        padding: 8px 16px;
        margin-right: 4px;
        border-bottom: 2px solid transparent;
        font-weight: 500;
    }}

    QTabBar::tab:hover {{
        color: {text};
        background: {surface_hover};
        border-radius: 4px 4px 0 0;
    }}

    QTabBar::tab:selected {{
        color: {accent};
        border-bottom: 2px solid {accent};
        font-weight: 600;
    }}

    QTabBar::close-button {{
        image: none;
        subcontrol-position: right;
        margin-left: 6px;
    }}

    /* Input Fields */
    QLineEdit, QTextEdit, QPlainTextEdit, QDateTimeEdit, QDateEdit, QTimeEdit, QComboBox {{
        background-color: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 6px 10px;
        selection-background-color: {accent};
        selection-color: #ffffff;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDateTimeEdit:focus, QComboBox:focus {{
        border: 1.5px solid {accent};
    }}

    /* Task Card Container */
    QFrame.taskCard {{
        background-color: {surface};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
    }}

    QFrame.taskCard:hover {{
        border-color: {accent};
    }}

    QFrame.subtaskCard {{
        background-color: {surface_hover};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 6px 10px;
        margin: 2px 0 2px 18px;
    }}

    /* Checkboxes */
    QCheckBox {{
        spacing: 8px;
        color: {text};
        font-size: 13px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {border};
        border-radius: 9px;
        background-color: {surface};
    }}

    QCheckBox::indicator:hover {{
        border-color: {accent};
    }}

    QCheckBox::indicator:checked {{
        background-color: {accent};
        border-color: {accent};
        image: none;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {border};
        border-radius: 4px;
        min-height: 24px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {text_muted};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background: {border};
        border-radius: 4px;
        min-width: 24px;
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* Badges & Labels */
    QLabel#badgeOverdue {{
        background-color: {danger};
        color: #ffffff;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 11px;
        font-weight: bold;
    }}

    QLabel#badgeToday {{
        background-color: {warning};
        color: #11111b;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 11px;
        font-weight: bold;
    }}

    QLabel#badgeUpcoming {{
        background-color: {border};
        color: {text_muted};
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 11px;
    }}

    QLabel#mutedText {{
        color: {text_muted};
        font-size: 12px;
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {surface};
        color: {text_muted};
        border-top: 1px solid {border};
        font-size: 11px;
    }}

    /* Menus & Dialogs */
    QMenu {{
        background-color: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 4px 0px;
    }}

    QMenu::item {{
        padding: 6px 24px 6px 12px;
    }}

    QMenu::item:selected {{
        background-color: {accent};
        color: #ffffff;
    }}

    QMessageBox, QDialog {{
        background-color: {bg};
        color: {text};
    }}
    """
