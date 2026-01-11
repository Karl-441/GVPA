from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt

class AppTheme:
    # --- Palettes ---
    
    # Nord (Default Dark)
    NORD_PALETTE = {
        "Window": "#2E3440",
        "WindowText": "#ECEFF4",
        "Base": "#3B4252",
        "AlternateBase": "#2E3440",
        "Text": "#ECEFF4",
        "Button": "#3B4252",
        "ButtonText": "#ECEFF4",
        "Highlight": "#5E81AC",
        "HighlightedText": "#FFFFFF",
        "Link": "#88C0D0"
    }
    
    # Tactical (GFL Style)
    TACTICAL_PALETTE = {
        "Window": "#1A1A1A",      # Deep Gray/Black
        "WindowText": "#F0F0F0",  # Off-white
        "Base": "#212121",        # Input background
        "AlternateBase": "#262626",
        "Text": "#F0F0F0",
        "Button": "#333333",
        "ButtonText": "#FDC800",  # Yellow Text on Buttons
        "Highlight": "#FDC800",   # Signature Yellow
        "HighlightedText": "#1A1A1A", # Black text on Yellow
        "Link": "#FDC800"
    }
    
    # Light
    LIGHT_PALETTE = {
        "Window": "#FFFFFF",
        "WindowText": "#000000",
        "Base": "#F5F5F5",
        "AlternateBase": "#E0E0E0",
        "Text": "#000000",
        "Button": "#E0E0E0",
        "ButtonText": "#000000",
        "Highlight": "#0078D7",
        "HighlightedText": "#FFFFFF",
        "Link": "#0000FF"
    }

    # Common Helper Colors
    BTN_PRIMARY = "#5E81AC"
    BTN_SUCCESS = "#A3BE8C"
    BTN_DANGER = "#BF616A"
    BTN_WARNING = "#EBCB8B"
    BTN_TEXT = "#FFFFFF"

    @staticmethod
    def get_btn_style(color_hex):
        # Default rounded style, can be overridden by global stylesheet
        return f"background-color: {color_hex}; color: {AppTheme.BTN_TEXT}; font-weight: bold; padding: 5px; border-radius: 4px;"

    @staticmethod
    def apply_theme(app, theme_name="Nord"):
        """Apply the specified theme to the application"""
        
        palette_data = AppTheme.NORD_PALETTE
        if theme_name == "Tactical":
            palette_data = AppTheme.TACTICAL_PALETTE
        elif theme_name == "Light":
            palette_data = AppTheme.LIGHT_PALETTE
            
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(palette_data["Window"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(palette_data["WindowText"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(palette_data["Base"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(palette_data["AlternateBase"]))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(palette_data["Window"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(palette_data["WindowText"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(palette_data["Text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(palette_data["Button"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(palette_data["ButtonText"]))
        palette.setColor(QPalette.ColorRole.Link, QColor(palette_data["Link"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(palette_data["Highlight"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(palette_data["HighlightedText"]))
        
        # Specific overrides for disabled states if needed
        # palette.setColor(QPalette.ColorRole.Disabled, QPalette.ColorRole.Text, QColor("#808080"))
        
        app.setPalette(palette)
        app.setStyle("Fusion") 

        # Apply Stylesheet for finer control (Borders, specific widgets)
        if theme_name == "Tactical":
            AppTheme.apply_tactical_stylesheet(app)
        else:
            # Reset or apply default
            app.setStyleSheet("") # Clear specific styles
            
            # Re-apply minimal base style if needed
            if theme_name == "Nord":
                 app.setStyleSheet("""
                    QToolTip { color: #ECEFF4; background-color: #2E3440; border: 1px solid #ECEFF4; }
                    QHeaderView::section { background-color: #3B4252; color: #ECEFF4; padding: 4px; border: 0px; }
                 """)

    @staticmethod
    def apply_tactical_stylesheet(app):
        """
        Apply GFL/Tactical style sheet.
        Features: Sharp corners, Yellow borders, Tech font feel.
        """
        yellow = "#FDC800"
        dark_bg = "#1A1A1A"
        panel_bg = "#212121"
        text_color = "#F0F0F0"
        
        qss = f"""
            /* Global Reset */
            QWidget {{
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 10pt;
            }}
            
            /* Main Window & Panels */
            QMainWindow, QDialog {{
                background-color: {dark_bg};
            }}
            
            /* Inputs */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {panel_bg};
                color: {text_color};
                border: 1px solid #444;
                border-radius: 0px; /* Sharp corners */
                padding: 4px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {yellow};
                background-color: #2a2a2a;
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: #333;
                color: {text_color};
                border: 1px solid #555;
                border-radius: 0px; /* Sharp */
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #444;
                border: 1px solid {yellow};
                color: {yellow};
            }}
            QPushButton:pressed {{
                background-color: {yellow};
                color: #000;
            }}
            
            /* Tab Widget */
            QTabWidget::pane {{
                border: 1px solid #444;
                background-color: {panel_bg};
            }}
            QTabBar::tab {{
                background-color: #1a1a1a;
                color: #888;
                border: 1px solid #333;
                border-bottom-color: #444;
                padding: 8px 16px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: {panel_bg};
                color: {yellow};
                border: 1px solid {yellow};
                border-bottom-color: {panel_bg}; /* Blend with pane */
            }}
            QTabBar::tab:hover {{
                color: {yellow};
            }}
            
            /* Lists & Trees */
            QTreeWidget, QListWidget {{
                background-color: {panel_bg};
                border: 1px solid #333;
                alternate-background-color: #262626;
            }}
            QTreeWidget::item:selected, QListWidget::item:selected {{
                background-color: {yellow};
                color: #000;
            }}
            QHeaderView::section {{
                background-color: #111;
                color: {yellow};
                border: 1px solid #333;
                padding: 4px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            
            /* Scrollbars (Webkit style for Qt) */
            QScrollBar:vertical {{
                border: none;
                background: #111;
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #444;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {yellow};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            /* Menu */
            QMenuBar {{
                background-color: #111;
                color: #ccc;
            }}
            QMenuBar::item:selected {{
                background-color: {yellow};
                color: #000;
            }}
            QMenu {{
                background-color: #222;
                border: 1px solid {yellow};
            }}
            QMenu::item {{
                padding: 5px 20px;
                color: #eee;
            }}
            QMenu::item:selected {{
                background-color: {yellow};
                color: #000;
            }}
            
            /* Tooltips */
            QToolTip {{
                background-color: rgba(20, 20, 20, 240);
                color: {yellow};
                border: 1px solid {yellow};
                padding: 4px;
            }}
        """
        app.setStyleSheet(qss)

    @staticmethod
    def apply_dark_theme(app):
        # Legacy support or alias to default Nord
        AppTheme.apply_theme(app, "Nord")
