# Pawtogen.py
import sys
import time
import threading
import pyautogui
import keyboard
import os
# FIX: Import pydirectinput for better game compatibility
import pydirectinput 
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, 
                            QSpinBox, QRadioButton, QButtonGroup, QGroupBox, QGridLayout,
                            QMessageBox, QCheckBox, QFrame, QGraphicsDropShadowEffect, QToolTip)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QPen, QBrush, QLinearGradient, QCursor

class ModernButton(QPushButton):
    def __init__(self, text, color="#4a90e2", hover_color="#3a7bc8", parent=None):
        super(ModernButton, self).__init__(text, parent)
        self.color = QColor(color)
        self.hover_color = QColor(hover_color)
        self.default_color = QColor(color)
        self.pressed_color = QColor("#2a5a98")
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: #2a5a98;
            }}
        """)
        
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(3)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)

class ModernGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super(ModernGroupBox, self).__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: #1e1e1e;
            }
        """)

# FIX: Modified ClickerThread for better responsiveness and error handling
class ClickerThread(QThread):
    def __init__(self, parent=None):
        super(ClickerThread, self).__init__(parent)
        self.running = False
        self.click_type = "single"
        self.button = "left"
        self.interval = 1.0
        self.current_count = 0

    def run(self):
        self.running = True
        self.current_count = 0
        
        try:
            while self.running:
                self.current_count += 1
                    
                if self.button == "left":
                    if self.click_type == "single":
                        pyautogui.click()
                    else:
                        pyautogui.doubleClick()
                else:  # right button
                    if self.click_type == "single":
                        pyautogui.rightClick()
                    else:
                        pyautogui.doubleClick(button='right')
                
                # FIX: Sleep in smaller increments to be more responsive to stop() signal
                sleep_time = self.interval
                while sleep_time > 0 and self.running:
                    time_to_sleep = min(0.1, sleep_time)  # Sleep in 0.1s increments
                    time.sleep(time_to_sleep)
                    sleep_time -= time_to_sleep
        except Exception as e:
            print(f"Error in ClickerThread: {e}")
        
        self.running = False

    def stop(self):
        self.running = False

# FIX: Modified KeyboardThread for better responsiveness and game compatibility
class KeyboardThread(QThread):
    def __init__(self, parent=None):
        super(KeyboardThread, self).__init__(parent)
        self.running = False
        self.key = "a"
        self.interval = 1.0
        self.current_count = 0

    def run(self):
        self.running = True
        self.current_count = 0
        
        try:
            while self.running:
                self.current_count += 1
                # FIX: Use pydirectinput for better game compatibility
                pydirectinput.press(self.key)
                
                # FIX: Sleep in smaller increments to be more responsive to stop() signal
                sleep_time = self.interval
                while sleep_time > 0 and self.running:
                    time_to_sleep = min(0.1, sleep_time)  # Sleep in 0.1s increments
                    time.sleep(time_to_sleep)
                    sleep_time -= time_to_sleep
        except Exception as e:
            print(f"Error in KeyboardThread: {e}")
        
        self.running = False

    def stop(self):
        self.running = False

class HotkeyDetector(QThread):
    hotkey_detected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(HotkeyDetector, self).__init__(parent)
        self.detecting = False
        
    def run(self):
        self.detecting = True
        while self.detecting:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                self.hotkey_detected.emit(event.name)
                break
                
    def stop(self):
        self.detecting = False

class StatusIndicator(QLabel):
    def __init__(self, parent=None):
        super(StatusIndicator, self).__init__(parent)
        self.setFixedSize(15, 15)
        self.status = "idle"  # idle, running, stopped
        
    def set_status(self, status):
        self.status = status
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.status == "idle":
            color = QColor("#555555")
        elif self.status == "running":
            color = QColor("#4CAF50")
        else:  # stopped
            color = QColor("#F44336")
            
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

class PawtogenApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pawtogen")
        self.setGeometry(100, 100, 700, 600)  # Changed to 700x540 as requested
        self.setFixedSize(700, 600)  # Window size fixed
        
        # Set application icon if icon.png exists
        self.set_app_icon()
        
        # Theme definitions
        self.themes = {
            "Default": {
                "bg": "#1e1e1e",
                "panel": "#2a2a2a",
                "border": "#3c3c3c",
                "accent": "#4a90e2",
                "hover": "#3a7bc8",
                "button": "#4a4a4a",
                "button_hover": "#5a5a5a",
                "text": "#ffffff",
                "text_secondary": "#888888"
            },
            "Snoozy": {
                "bg": "#0a1929",
                "panel": "#132f4c",
                "border": "#1e3a5f",
                "accent": "#4a90e2",
                "hover": "#357abd",
                "button": "#1e4976",
                "button_hover": "#295a8f",
                "text": "#e0e0e0",
                "text_secondary": "#a0a0a0"
            },
            "Bobber": {
                "bg": "#1a1a1a",
                "panel": "#252525",
                "border": "#333333",
                "accent": "#ff00ff",  # Will be animated
                "hover": "#ff00ff",  # Will be animated
                "button": "#2a2a2a",
                "button_hover": "#3a3a3a",
                "text": "#ffffff",
                "text_secondary": "#aaaaaa"
            }
        }
        
        self.current_theme = "Default"
        self.rgb_animation_timer = QTimer()
        self.rgb_animation_timer.timeout.connect(self.update_rgb_theme)
        self.rgb_hue = 0
        
        self.clicker_thread = ClickerThread()
        self.keyboard_thread = KeyboardThread()
        self.hotkey_detector = HotkeyDetector()
        self.hotkey_detector.hotkey_detected.connect(self.on_hotkey_detected)
        
        # Default hotkeys - Changed F1 to F6 for autoclicker
        self.mouse_hotkey = "f6"
        self.keyboard_hotkey = "f2"
        
        self.init_ui()
        self.apply_theme("Default")
        self.setup_hotkeys()
        
    # FIX: Added closeEvent method to properly clean up resources when closing the application
    def closeEvent(self, event):
        # Clean up threads
        if self.clicker_thread.isRunning():
            self.clicker_thread.stop()
            self.clicker_thread.wait()
        
        if self.keyboard_thread.isRunning():
            self.keyboard_thread.stop()
            self.keyboard_thread.wait()
        
        if self.hotkey_detector.isRunning():
            self.hotkey_detector.stop()
            self.hotkey_detector.wait()
        
        # Unhook all keyboard hotkeys
        keyboard.unhook_all()
        
        # Accept the close event
        event.accept()
    
    def set_app_icon(self):
        # Try to load icon.png from the same directory as the script
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
            if os.path.exists(icon_path):
                app_icon = QIcon(icon_path)
                self.setWindowIcon(app_icon)
                # Also set the application icon for the taskbar
                QApplication.instance().setWindowIcon(app_icon)
        except Exception as e:
            print(f"Could not load icon: {e}")
    
    def init_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add header with logo
        header_layout = QHBoxLayout()
        
        # Logo placeholder (load icon.png instead of blue box)
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(50, 50)
        
        # Try to load icon.png from the same directory as the script
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
            if os.path.exists(icon_path):
                logo_pixmap = QPixmap(icon_path)
                # Scale the image to fit the 50x50 container while maintaining aspect ratio
                logo_pixmap = logo_pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(logo_pixmap)
            else:
                # Create a placeholder if the file doesn't exist
                logo_pixmap = QPixmap(50, 50)
                logo_pixmap.fill(QColor("#4a90e2"))
                self.logo_label.setPixmap(logo_pixmap)
        except Exception as e:
            print(f"Could not load logo: {e}")
            # Create a placeholder if there's an error
            logo_pixmap = QPixmap(50, 50)
            logo_pixmap.fill(QColor("#4a90e2"))
            self.logo_label.setPixmap(logo_pixmap)
        
        header_layout.addWidget(self.logo_label)
        
        # Title
        self.title_label = QLabel("PAWTOGEN")
        self.title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #4a90e2;
            letter-spacing: 2px;
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Version label
        self.version_label = QLabel("v1.0")
        self.version_label.setStyleSheet("""
            font-size: 12px;
            color: #888888;
        """)
        header_layout.addWidget(self.version_label)
        
        main_layout.addLayout(header_layout)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.mouse_tab = QWidget()
        self.key_tab = QWidget()
        self.settings_tab = QWidget()
        self.credits_tab = QWidget()
        
        # Add tabs to widget
        self.tabs.addTab(self.mouse_tab, "Mouse")
        self.tabs.addTab(self.key_tab, "Key")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.credits_tab, "Credits")
        
        main_layout.addWidget(self.tabs)
        
        # Add footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        status_text = QLabel("STATUS")
        status_text.setStyleSheet("""
            font-size: 10px;
            color: #888888;
            letter-spacing: 1px;
        """)
        footer_layout.addWidget(status_text)
        
        self.mouse_status_indicator = StatusIndicator()
        footer_layout.addWidget(self.mouse_status_indicator)
        
        self.key_status_indicator = StatusIndicator()
        footer_layout.addWidget(self.key_status_indicator)
        
        main_layout.addLayout(footer_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Setup each tab
        self.setup_mouse_tab()
        self.setup_key_tab()
        self.setup_settings_tab()
        self.setup_credits_tab()
        
    def apply_theme(self, theme_name):
        theme = self.themes[theme_name]
        self.current_theme = theme_name
        
        # Stop RGB animation if switching away from Bobber theme
        if theme_name != "Bobber":
            self.rgb_animation_timer.stop()
        else:
            # Start RGB animation for Bobber theme
            self.rgb_animation_timer.start(50)  # Update every 50ms for smooth animation
        
        # Apply theme to main window
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['bg']};
                color: {theme['text']};
            }}
            QTabWidget::pane {{
                border: 1px solid {theme['border']};
                background-color: {theme['panel']};
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background-color: {theme['panel']};
                color: {theme['text']};
                padding: 12px 30px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme['border']};
                border-bottom: 2px solid {theme['accent']};
            }}
            QTabBar::tab:hover {{
                background-color: {theme['button']};
            }}
            QLabel {{
                color: {theme['text']};
                font-size: 14px;
            }}
            QLineEdit, QSpinBox, QComboBox {{
                background-color: {theme['button']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 8px;
                border-radius: 5px;
                font-size: 14px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                subcontrol-origin: border;
                width: 20px;
                border-left: 1px solid {theme['border']};
                background-color: {theme['button_hover']};
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {theme['border']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                width: 20px;
                border-left: 1px solid {theme['border']};
                background-color: {theme['button_hover']};
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }}
            QComboBox::drop-down:hover {{
                background-color: {theme['border']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['button']};
                color: {theme['text']};
                selection-background-color: {theme['accent']};
                border: 1px solid {theme['border']};
            }}
            QRadioButton {{
                color: {theme['text']};
                font-size: 14px;
                spacing: 10px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            QRadioButton::indicator:unchecked {{
                border: 2px solid {theme['border']};
                border-radius: 8px;
                background-color: {theme['button']};
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {theme['accent']};
                border-radius: 8px;
                background-color: {theme['accent']};
            }}
            QCheckBox {{
                color: {theme['text']};
            }}
            QCheckBox::indicator {{
                width: 50px;
                height: 25px;
                border-radius: 12px;
                background-color: {theme['button']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme['accent']};
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {theme['button']};
            }}
            QCheckBox::indicator::before {{
                content: "";
                display: block;
                width: 21px;
                height: 21px;
                border-radius: 10px;
                background-color: white;
                position: absolute;
                top: 2px;
                left: 2px;
            }}
            QCheckBox::indicator:checked::before {{
                left: 27px;
            }}
        """)
        
        # Update title color
        self.title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {theme['accent']};
            letter-spacing: 2px;
        """)
        
        # Update version color
        self.version_label.setStyleSheet(f"""
            font-size: 12px;
            color: {theme['text_secondary']};
        """)
        
        # Update group boxes
        for group in self.findChildren(QGroupBox):
            group.setStyleSheet(f"""
                QGroupBox {{
                    color: {theme['text']};
                    border: 1px solid {theme['border']};
                    border-radius: 8px;
                    margin-top: 15px;
                    padding-top: 15px;
                    font-weight: bold;
                    font-size: 14px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 15px;
                    padding: 0 8px 0 8px;
                    background-color: {theme['bg']};
                }}
            """)
    
    def update_rgb_theme(self):
        """Update RGB colors for Bobber theme"""
        if self.current_theme != "Bobber":
            return
        
        # Calculate RGB from hue
        self.rgb_hue = (self.rgb_hue + 2) % 360
        rgb_color = QColor.fromHsv(self.rgb_hue, 255, 255)
        rgb_hex = rgb_color.name()
        
        # Update theme colors
        self.themes["Bobber"]["accent"] = rgb_hex
        self.themes["Bobber"]["hover"] = rgb_hex
        
        # Reapply theme with new colors
        self.apply_theme("Bobber")
    
    def setup_mouse_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Click Interval Group
        interval_group = ModernGroupBox("Click Interval")
        interval_layout = QGridLayout()
        
        interval_layout.addWidget(QLabel("Hours:"), 0, 0)
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setValue(0)
        interval_layout.addWidget(self.hours_spin, 0, 1)
        
        interval_layout.addWidget(QLabel("Minutes:"), 0, 2)
        self.mins_spin = QSpinBox()
        self.mins_spin.setRange(0, 59)
        self.mins_spin.setValue(0)
        interval_layout.addWidget(self.mins_spin, 0, 3)
        
        interval_layout.addWidget(QLabel("Seconds:"), 1, 0)
        self.secs_spin = QSpinBox()
        self.secs_spin.setRange(0, 59)
        self.secs_spin.setValue(1)
        interval_layout.addWidget(self.secs_spin, 1, 1)
        
        interval_layout.addWidget(QLabel("Milliseconds:"), 1, 2)
        self.ms_spin = QSpinBox()
        self.ms_spin.setRange(0, 999)
        self.ms_spin.setValue(0)
        interval_layout.addWidget(self.ms_spin, 1, 3)
        
        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)
        
        # Mouse Button Group
        button_group = ModernGroupBox("Mouse Button")
        button_layout = QHBoxLayout()
        
        self.button_group = QButtonGroup()
        self.left_radio = QRadioButton("Left")
        self.right_radio = QRadioButton("Right")
        self.left_radio.setChecked(True)
        
        self.button_group.addButton(self.left_radio, 0)
        self.button_group.addButton(self.right_radio, 1)
        
        button_layout.addWidget(self.left_radio)
        button_layout.addWidget(self.right_radio)
        button_group.setLayout(button_layout)
        layout.addWidget(button_group)
        
        # Click Type Group
        click_type_group = ModernGroupBox("Click Type")
        click_type_layout = QHBoxLayout()
        
        self.click_type_group = QButtonGroup()
        self.single_radio = QRadioButton("Single")
        self.double_radio = QRadioButton("Double")
        self.single_radio.setChecked(True)
        
        self.click_type_group.addButton(self.single_radio, 0)
        self.click_type_group.addButton(self.double_radio, 1)
        
        click_type_layout.addWidget(self.single_radio)
        click_type_layout.addWidget(self.double_radio)
        click_type_group.setLayout(click_type_layout)
        layout.addWidget(click_type_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_clicker_btn = ModernButton("Start Clicker", "#4CAF50", "#45a049")
        self.start_clicker_btn.clicked.connect(self.start_clicker)
        button_layout.addWidget(self.start_clicker_btn)
        
        self.stop_clicker_btn = ModernButton("Stop Clicker", "#F44336", "#d32f2f")
        self.stop_clicker_btn.clicked.connect(self.stop_clicker)
        self.stop_clicker_btn.setEnabled(False)
        button_layout.addWidget(self.stop_clicker_btn)
        
        layout.addLayout(button_layout)
        
        # Status label
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.clicker_status = QLabel("Idle")
        self.clicker_status.setStyleSheet("""
            color: #888888;
            font-style: italic;
        """)
        status_layout.addWidget(self.clicker_status)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        layout.addStretch()
        
        self.mouse_tab.setLayout(layout)
        
    def setup_key_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Key Selection Group
        key_group = ModernGroupBox("Key Selection")
        key_layout = QHBoxLayout()
        
        key_layout.addWidget(QLabel("Key:"))
        self.key_combo = QComboBox()
        self.key_combo.addItems([
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'space', 'enter', 'tab', 'esc', 'shift', 'ctrl', 'alt',
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12'
        ])
        key_layout.addWidget(self.key_combo)
        
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Interval Group
        interval_group = ModernGroupBox("Interval")
        interval_layout = QGridLayout()
        
        interval_layout.addWidget(QLabel("Hours:"), 0, 0)
        self.key_hours_spin = QSpinBox()
        self.key_hours_spin.setRange(0, 23)
        self.key_hours_spin.setValue(0)
        interval_layout.addWidget(self.key_hours_spin, 0, 1)
        
        interval_layout.addWidget(QLabel("Minutes:"), 0, 2)
        self.key_mins_spin = QSpinBox()
        self.key_mins_spin.setRange(0, 59)
        self.key_mins_spin.setValue(0)
        interval_layout.addWidget(self.key_mins_spin, 0, 3)
        
        interval_layout.addWidget(QLabel("Seconds:"), 1, 0)
        self.key_secs_spin = QSpinBox()
        self.key_secs_spin.setRange(0, 59)
        self.key_secs_spin.setValue(1)
        interval_layout.addWidget(self.key_secs_spin, 1, 1)
        
        interval_layout.addWidget(QLabel("Milliseconds:"), 1, 2)
        self.key_ms_spin = QSpinBox()
        self.key_ms_spin.setRange(0, 999)
        self.key_ms_spin.setValue(0)
        interval_layout.addWidget(self.key_ms_spin, 1, 3)
        
        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_key_btn = ModernButton("Start Keyboard Macro", "#4CAF50", "#45a049")
        self.start_key_btn.clicked.connect(self.start_keyboard)
        button_layout.addWidget(self.start_key_btn)
        
        self.stop_key_btn = ModernButton("Stop Keyboard Macro", "#F44336", "#d32f2f")
        self.stop_key_btn.clicked.connect(self.stop_keyboard)
        self.stop_key_btn.setEnabled(False)
        button_layout.addWidget(self.stop_key_btn)
        
        layout.addLayout(button_layout)
        
        # Status label
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.key_status = QLabel("Idle")
        self.key_status.setStyleSheet("""
            color: #888888;
            font-style: italic;
        """)
        status_layout.addWidget(self.key_status)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        layout.addStretch()
        
        self.key_tab.setLayout(layout)
        
    def setup_settings_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Theme Selector Group
        theme_group = ModernGroupBox("Theme")
        theme_layout = QHBoxLayout()
        
        theme_layout.addWidget(QLabel("Select Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Snoozy", "Bobber"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Hotkeys Group
        hotkey_group = ModernGroupBox("Hotkeys")
        hotkey_layout = QGridLayout()
        
        hotkey_layout.addWidget(QLabel("Mouse Clicker Hotkey:"), 0, 0)
        self.mouse_hotkey_btn = ModernButton(self.mouse_hotkey.upper(), "#3c3c3c", "#4a4a4a")
        self.mouse_hotkey_btn.clicked.connect(lambda: self.detect_hotkey("mouse"))
        hotkey_layout.addWidget(self.mouse_hotkey_btn, 0, 1)
        
        hotkey_layout.addWidget(QLabel("Keyboard Macro Hotkey:"), 1, 0)
        self.keyboard_hotkey_btn = ModernButton(self.keyboard_hotkey.upper(), "#3c3c3c", "#4a4a4a")
        self.keyboard_hotkey_btn.clicked.connect(lambda: self.detect_hotkey("keyboard"))
        hotkey_layout.addWidget(self.keyboard_hotkey_btn, 1, 1)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # Instructions
        instructions_group = ModernGroupBox("Instructions")
        instructions_layout = QVBoxLayout()
        
        instructions_text = QLabel(
            "1. Click on a hotkey button to change it\n"
            "2. Press any key to set as the new hotkey\n"
            "3. The hotkey will toggle the corresponding function on/off\n"
            "4. Make sure the Pawtogen window is not minimized when using hotkeys"
        )
        instructions_text.setWordWrap(True)
        instructions_layout.addWidget(instructions_text)
        
        instructions_group.setLayout(instructions_layout)
        layout.addWidget(instructions_group)
        
        layout.addStretch()
        
        self.settings_tab.setLayout(layout)
        
    def setup_credits_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Logo container
        logo_container = QWidget()
        logo_container.setFixedSize(200, 200)
        logo_layout = QVBoxLayout(logo_container)
        
        logo_label = QLabel()
        
        # Try to load logocreds.png from the same directory as the script
        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logocreds.png")
            if os.path.exists(logo_path):
                logo_pixmap = QPixmap(logo_path)
                # Scale the image to fit the container while maintaining aspect ratio
                logo_pixmap = logo_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                # Create a placeholder if the file doesn't exist
                logo_pixmap = QPixmap(200, 200)
                painter = QPainter(logo_pixmap)
                gradient = QLinearGradient(0, 0, 200, 200)
                gradient.setColorAt(0, QColor("#4a90e2"))
                gradient.setColorAt(1, QColor("#2a5a98"))
                painter.fillRect(0, 0, 200, 200, QBrush(gradient))
                
                # Add a simple "P" text to the logo
                painter.setPen(QPen(QColor("#ffffff"), 5))
                painter.setFont(QFont("Arial", 100, QFont.Bold))
                painter.drawText(logo_pixmap.rect(), Qt.AlignCenter, "P")
                painter.end()
        except Exception as e:
            print(f"Could not load logo: {e}")
            # Create a placeholder if there's an error
            logo_pixmap = QPixmap(200, 200)
            painter = QPainter(logo_pixmap)
            gradient = QLinearGradient(0, 0, 200, 200)
            gradient.setColorAt(0, QColor("#4a90e2"))
            gradient.setColorAt(1, QColor("#2a5a98"))
            painter.fillRect(0, 0, 200, 200, QBrush(gradient))
            
            # Add a simple "P" text to the logo
            painter.setPen(QPen(QColor("#ffffff"), 5))
            painter.setFont(QFont("Arial", 100, QFont.Bold))
            painter.drawText(logo_pixmap.rect(), Qt.AlignCenter, "P")
            painter.end()
        
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        logo_container_layout = QHBoxLayout()
        logo_container_layout.addStretch()
        logo_container_layout.addWidget(logo_container)
        logo_container_layout.addStretch()
        layout.addLayout(logo_container_layout)
        
        # Credits text
        credits_text = QLabel(
            "<h2 style='color: #4a90e2;'>Pawtogen</h2>"
            "<p style='font-size: 16px;'>Advanced Autoclicker & Keyboard Tool</p>"
            "<p style='font-size: 16px;'>Created by: Banii</p>"
            "<p style='font-size: 14px; color: #888888;'>@baniisama</p>"
            "<p style='font-size: 14px; color: #888888;'>Version: 1.0</p>"
            "<p style='font-size: 14px; color: #888888;'>Made with 🐱, For personal use only</p>"
        )
        credits_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits_text)
        
        # Add some spacing
        layout.addStretch()
        
        self.credits_tab.setLayout(layout)
        
    def on_theme_changed(self, theme_name):
        self.apply_theme(theme_name)
        
    def start_clicker(self):
        # Calculate interval in seconds
        hours = self.hours_spin.value()
        mins = self.mins_spin.value()
        secs = self.secs_spin.value()
        ms = self.ms_spin.value()
        
        interval = hours * 3600 + mins * 60 + secs + ms / 1000.0
        
        if interval <= 0:
            QMessageBox.warning(self, "Invalid Interval", "Please set a valid interval greater than 0.")
            return
            
        # Configure clicker thread
        self.clicker_thread.click_type = "single" if self.single_radio.isChecked() else "double"
        self.clicker_thread.button = "left" if self.left_radio.isChecked() else "right"
        self.clicker_thread.interval = interval
        
        # Start the thread
        self.clicker_thread.start()
        
        # Update UI
        self.start_clicker_btn.setEnabled(False)
        self.stop_clicker_btn.setEnabled(True)
        self.clicker_status.setText("Running")
        self.clicker_status.setStyleSheet("""
            color: #4CAF50;
            font-style: italic;
        """)
        self.mouse_status_indicator.set_status("running")
        
    def stop_clicker(self):
        self.clicker_thread.stop()
        self.clicker_thread.wait()
        
        # Update UI
        self.start_clicker_btn.setEnabled(True)
        self.stop_clicker_btn.setEnabled(False)
        self.clicker_status.setText(f"Stopped (Clicked {self.clicker_thread.current_count} times)")
        self.clicker_status.setStyleSheet("""
            color: #F44336;
            font-style: italic;
        """)
        self.mouse_status_indicator.set_status("stopped")
        
    def start_keyboard(self):
        # Calculate interval in seconds
        hours = self.key_hours_spin.value()
        mins = self.key_mins_spin.value()
        secs = self.key_secs_spin.value()
        ms = self.key_ms_spin.value()
        
        interval = hours * 3600 + mins * 60 + secs + ms / 1000.0
        
        if interval <= 0:
            QMessageBox.warning(self, "Invalid Interval", "Please set a valid interval greater than 0.")
            return
            
        # Configure keyboard thread
        self.keyboard_thread.key = self.key_combo.currentText()
        self.keyboard_thread.interval = interval
        
        # Start the thread
        self.keyboard_thread.start()
        
        # Update UI
        self.start_key_btn.setEnabled(False)
        self.stop_key_btn.setEnabled(True)
        self.key_status.setText("Running")
        self.key_status.setStyleSheet("""
            color: #4CAF50;
            font-style: italic;
        """)
        self.key_status_indicator.set_status("running")
        
    def stop_keyboard(self):
        self.keyboard_thread.stop()
        self.keyboard_thread.wait()
        
        # Update UI
        self.start_key_btn.setEnabled(True)
        self.stop_key_btn.setEnabled(False)
        self.key_status.setText(f"Stopped (Pressed {self.keyboard_thread.current_count} times)")
        self.key_status.setStyleSheet("""
            color: #F44336;
            font-style: italic;
        """)
        self.key_status_indicator.set_status("stopped")
        
    def detect_hotkey(self, hotkey_type):
        # Store which hotkey is being changed
        self.hotkey_type = hotkey_type
        
        # Show "Listening..." on the button
        if hotkey_type == "mouse":
            self.mouse_hotkey_btn.setText("Listening...")
            self.mouse_hotkey_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
        else:
            self.keyboard_hotkey_btn.setText("Listening...")
            self.keyboard_hotkey_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
        
        # Start hotkey detection
        self.hotkey_detector.start()
        
    def on_hotkey_detected(self, key):
        # Stop detection
        self.hotkey_detector.stop()
        self.hotkey_detector.wait()
        
        # Update hotkey
        if self.hotkey_type == "mouse":
            self.mouse_hotkey = key
            self.mouse_hotkey_btn.setText(key.upper())
            self.mouse_hotkey_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
            """)
        else:
            self.keyboard_hotkey = key
            self.keyboard_hotkey_btn.setText(key.upper())
            self.keyboard_hotkey_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
            """)
            
        # Re-setup hotkeys
        self.setup_hotkeys()
        
    def setup_hotkeys(self):
        # Clear existing hotkeys
        keyboard.unhook_all()
        
        # Setup new hotkeys
        keyboard.add_hotkey(self.mouse_hotkey, self.toggle_clicker)
        keyboard.add_hotkey(self.keyboard_hotkey, self.toggle_keyboard)
        
    def toggle_clicker(self):
        if self.clicker_thread.isRunning():
            self.stop_clicker()
        else:
            self.start_clicker()
            
    def toggle_keyboard(self):
        if self.keyboard_thread.isRunning():
            self.stop_keyboard()
        else:
            self.start_keyboard()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PawtogenApp()
    window.show()
    sys.exit(app.exec_())