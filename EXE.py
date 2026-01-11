import sys
import subprocess
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QComboBox, QMessageBox, QCheckBox, QGroupBox, QScrollArea
)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

TOOLS = [
    ("Nuitka", "nuitka"),
    ("PyInstaller", "pyinstaller"),
    ("cx_Freeze", "cx_Freeze"),
    ("py2exe (Windows only)", "py2exe"),
    ("pyoxidizer", "pyoxidizer"),
    ("auto-py-to-exe", "auto-py-to-exe"),
]

TOOL_EXPLAIN = [
    "Nuitka (best protection: compiles to C/machine code) — Use with PyQt5 via Qt plugin!",
    "PyInstaller (easy, common, cross-platform)",
    "cx_Freeze (simple, multiplatform)",
    "py2exe (Windows only, legacy)",
    "pyoxidizer (advanced, single binary)",
    "auto-py-to-exe (PyInstaller GUI, beginner-friendly)",
]

TOOL_FLAGS = [
    # Nuitka
    [
        ("--onefile", "Bundle into one executable"),
        ("--standalone", "Include all dependencies (portable)"),
        ("--show-progress", "Show build progress"),
        ("--noinclude-pytest-mode=nofollow", "Smaller EXE (strip pytest support)"),
        ("--mingw64", "Use MinGW64 as C compiler (Windows only)"),
        ("--windows-icon-from-ico=app.ico", "Custom app icon (replace path as needed)"),
        ("--enable-plugin=pyqt5", "Enable PyQt5 plugin support for Qt GUIs in Nuitka"),
        ("--include-qt-plugins=sensible", "Bundle sensible set of Qt plugins (most GUIs)"),
    ],
    # PyInstaller
    [
        ("--onefile", "Bundle into a single exe"),
        ("--console", "Enable console window (needed for input())"),
        ("--windowed", "No console window (GUI apps only)"),
        ("--icon=app.ico", "Custom app icon (replace path as needed)"),
        ("--clean", "Clean up temp files first"),
        ("--add-data=data.file;.", "Add external data file (replace as needed)"),
    ],
    # cx_Freeze
    [
        ("base=None", "Console app (allows input())"),
        ("base=Win32GUI", "GUI app (no console)"),
        ("include_files", "Add extra files (use in setup.py)"),
        ("silent=True", "Suppress cx_Freeze output"),
    ],
    # py2exe
    [
        ("console", "Console app (allows input())"),
        ("windows", "GUI/windowed app"),
        ("bundle_files=1", "Try single exe (not recommended for complex apps)"),
        ("compressed=True", "Compress the library zip"),
    ],
    # pyoxidizer
    [
        ("single_binary=True", "Bundle everything in one binary (edit oxidizer.bzl)"),
        ("--release", "Release mode build (smaller binary)"),
        ("--debug", "Debug mode build"),
    ],
    # auto-py-to-exe
    []
]

def set_dark_mode(app):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

def get_install_commands(tool):
    return f"""
{tool} is required.

Try these commands:
    pip install {tool}
or:
    python -m pip install {tool}
"""

def ensure_installed(tool, parent_widget=None):
    try:
        __import__(tool)
        return True
    except ImportError:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", tool], check=True)
            return True
        except Exception:
            if parent_widget:
                QMessageBox.warning(parent_widget, "Missing Dependency", get_install_commands(tool))
            return False

class ExeBuilderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python EXE Builder With Dynamic Options")
        self.setGeometry(90, 90, 780, 540)
        self.file_path = None
        self._init_ui()

    def _init_ui(self):
        widget = QWidget(self)
        self.layout = QVBoxLayout(widget)
        self.status = QLabel("Select a Python script and builder. Then check attributes to use.", self)
        self.layout.addWidget(self.status)

        self.select_btn = QPushButton("Select Python File", self)
        self.select_btn.clicked.connect(self.select_file)
        self.layout.addWidget(self.select_btn)

        self.method_box = QComboBox(self)
        for text in TOOL_EXPLAIN:
            self.method_box.addItem(text)
        self.method_box.currentIndexChanged.connect(self.show_flag_checkboxes)
        self.layout.addWidget(self.method_box)

        # Dynamic options area
        self.flags_group = QGroupBox("Options")
        self.flags_layout = QVBoxLayout()
        self.flags_group.setLayout(self.flags_layout)

        # Add scrolling in case there are many options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.flags_group)
        self.layout.addWidget(scroll)

        self.checkboxes = []

        self.build_btn = QPushButton("Build EXE (No Obfuscation)", self)
        self.build_btn.clicked.connect(self.build_exe)
        self.layout.addWidget(self.build_btn)

        self.setCentralWidget(widget)
        self.show_flag_checkboxes()

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Python File", "", "Python Files (*.py)")
        if file:
            self.file_path = file
            self.status.setText(f"Selected: {os.path.basename(file)}")

    def show_flag_checkboxes(self):
        for i in reversed(range(self.flags_layout.count())):
            w = self.flags_layout.itemAt(i).widget()
            if w is not None:
                self.flags_layout.removeWidget(w)
                w.deleteLater()
        self.checkboxes = []
        idx = self.method_box.currentIndex()
        for flag, explanation in TOOL_FLAGS[idx]:
            cb = QCheckBox(f"{flag} ({explanation})")
            self.flags_layout.addWidget(cb)
            self.checkboxes.append(cb)
        if idx == 5:
            lab = QLabel("Use the GUI to set all options for PyInstaller visually.")
            self.flags_layout.addWidget(lab)

    def build_exe(self):
        if not self.file_path:
            self.status.setText("Please select a Python file first.")
            return
        method_idx = self.method_box.currentIndex()
        tool_name = TOOLS[method_idx][1]
        if not ensure_installed(tool_name, self):
            self.status.setText(f"{tool_name} not available.")
            return

        flags = []
        for i, cb in enumerate(self.checkboxes):
            if cb.isChecked():
                flag_or_opt = TOOL_FLAGS[method_idx][i][0]
                flags.append(flag_or_opt)
        try:
            if method_idx == 0: # Nuitka
                cmd = [sys.executable, "-m", "nuitka", self.file_path] + flags
                subprocess.run(cmd, check=True)
                self.status.setText("EXE built with Nuitka (output folder).")
            elif method_idx == 1: # PyInstaller
                cmd = [sys.executable, "-m", "PyInstaller", self.file_path] + flags + ["--hidden-import=colorama"]
                subprocess.run(cmd, check=True)
                self.status.setText("EXE built with PyInstaller (dist folder).")
            elif method_idx == 2: # cx_Freeze
                base = None
                if "base=Win32GUI" in flags:
                    base = "Win32GUI"
                setup_code = f"""
from cx_Freeze import setup, Executable
setup(
    name="{os.path.splitext(os.path.basename(self.file_path))[0]}",
    version="0.1",
    executables=[Executable("{self.file_path}"{', base="Win32GUI"' if base=="Win32GUI" else ''})]
)
"""
                import tempfile
                temp_dir = tempfile.mkdtemp()
                setup_path = os.path.join(temp_dir, "setup.py")
                with open(setup_path, "w") as f:
                    f.write(setup_code)
                subprocess.run([sys.executable, setup_path, "build"], cwd=temp_dir, check=True)
                self.status.setText("EXE built with cx_Freeze (build folder in temp dir).")
            elif method_idx == 3: # py2exe
                console = "console" in flags
                windows = "windows" in flags
                if not (console or windows):
                    console = True
                setup_code = f"""
from distutils.core import setup
import py2exe
setup({"console" if console else "windows"}=['{self.file_path}'])
"""
                import tempfile
                temp_dir = tempfile.mkdtemp()
                setup_path = os.path.join(temp_dir, "setup_py2exe.py")
                with open(setup_path, "w") as f:
                    f.write(setup_code)
                subprocess.run([sys.executable, setup_path, "py2exe"], cwd=temp_dir, check=True)
                self.status.setText("EXE built with py2exe (dist folder in temp dir).")
            elif method_idx == 4: # pyoxidizer
                cmd = ["pyoxidizer", "init-config", self.file_path]
                subprocess.run(cmd, check=True)
                cmd2 = ["pyoxidizer", "build"]
                if "--release" in flags:
                    cmd2.append("--release")
                if "--debug" in flags:
                    cmd2.append("--debug")
                subprocess.run(cmd2, check=True)
                self.status.setText("EXE built with pyoxidizer (see build artifacts).")
            elif method_idx == 5: # auto-py-to-exe
                cmd = ["auto-py-to-exe"]
                subprocess.Popen(cmd)
                self.status.setText("Opened auto-py-to-exe GUI. Use it to build your EXE.")
        except Exception as e:
            self.status.setText(f"Build failed: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_dark_mode(app)
    win = ExeBuilderApp()
    win.show()
    sys.exit(app.exec_())
