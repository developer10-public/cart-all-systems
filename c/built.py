
import os
import re
import queue
import subprocess as sp
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QTextEdit, QSplitter, QFileDialog
)
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QTextCursor, QSyntaxHighlighter
from PyQt5.QtCore import Qt, QTimer
    
_version_ = 1.0
compiler = r"C:\Users\HP\Downloads\IDE-for-programming-languages-1.0.1\IDE-for-programming-languages-1.0.1\compile_lib\ucrt64\bin\gcc.exe"
class C_SyntaxHighlighter(QSyntaxHighlighter):
    """Safe, native PyQt5 syntax highlighter that won't crash the editor loops."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.formats = {}
        self.setup_formats()

    def setup_formats(self):
        # Keyword Style
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#0048A7"))
        fmt.setFontWeight(QFont.Weight.Bold)
        self.formats["keyword"] = fmt
        
        # Type Style
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#0048a7"))
        fmt.setFontWeight(QFont.Bold)
        self.formats["type"] = fmt
        
        # String Style
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#CE9178"))
        self.formats["string"] = fmt
        
        # Comment Style
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#608B4E"))
        self.formats["comment"] = fmt
        
        # Include Style
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#C586C0"))
        self.formats["include"] = fmt
        
        # Function Style
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#FFF676"))
        self.formats["function"] = fmt
        
        # Variable Style
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#63C9F8"))
        self.formats["var"] = fmt

        # Error Style (Missing Semicolon / Bad Include)
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#FFCCCC"))
        fmt.setForeground(QColor("#FF0000"))
        fmt.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.formats["error"] = fmt

    def highlightBlock(self, text):
        clean_line = text.strip()
        if not clean_line:
            return

        # 1. Handle Include Check (Strict C Rules)
        if clean_line.startswith("#include"):
            include_match = re.search(r'#include\s*(<[a-zA-Z0-9_\+/\.]+\.h>|"[a-zA-Z0-9_\+/\.]+\.h")\s*$', text)
            if include_match:
                self.setFormat(0, len(text), self.formats["include"])
            else:
                self.setFormat(0, len(text), self.formats["error"])
            return  

        # 2. Comments
        comment_match = re.search(r'//.*', text)
        if comment_match:
            self.setFormat(comment_match.start(), comment_match.end() - comment_match.start(), self.formats["comment"])
            if clean_line.startswith("//"):
                return

        # --- FIX: TRACK STRING RANGES TO PREVENT OVERWRITING ---
        string_ranges = []
        for match in re.finditer(r'".*?"|\'.*?\'', text):
            start = match.start()
            length = match.end() - start
            string_ranges.append((start, match.end()))
            self.setFormat(start, length, self.formats["string"])

        # Helper function to check if a match lands inside a literal string
        def is_inside_string(start_pos, end_pos):
            for s_start, s_end in string_ranges:
                if start_pos >= s_start and end_pos <= s_end:
                    return True
            return False

        # 3. Base Regex Rules (Only apply if NOT inside a string literal)
        keywords = r'\b(auto|break|case|const|continue|default|do|else|enum|extern|for|goto|if|inline|register|restrict|return|sizeof|static|struct|switch|typedef|union|volatile|while|_Alignas|_Alignof|_Atomic|_Generic|_Imaginary|_Noreturn|_Static_assert|_Thread_local)\b'
        types = r'\b(bool|char|double|float|int|long|short|signed|unsigned|void|_Bool|_Complex)\b'

        # Highlight Keywords
        for match in re.finditer(keywords, text):
            if not is_inside_string(match.start(), match.end()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats["keyword"])

        # Highlight Types
        for match in re.finditer(types, text):
            if not is_inside_string(match.start(), match.end()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats["type"])

        # Highlight Functions
        for match in re.finditer(r'\b(?!(?:if|for|while|switch|return)\b)[a-zA-Z_]\w*(?=\s*\()', text):
            if not is_inside_string(match.start(), match.end()):
                self.setFormat(match.start(), match.end() - match.start(), self.formats["function"])

        # Highlight Variables
        for type_match in re.finditer(types, text):
            if is_inside_string(type_match.start(), type_match.end()):
                continue
            type_end = type_match.end()
            remaining_line = text[type_end:]
            var_match = re.match(r'^[\s\*&]+([a-zA-Z_]\w*)\b(?!\s*\()', remaining_line)
            if var_match:
                var_name = var_match.group(1)
                var_start_col = type_end + remaining_line.find(var_name)
                if not is_inside_string(var_start_col, var_start_col + len(var_name)):
                    self.setFormat(var_start_col, len(var_name), self.formats["var"])

        # 4. Semicolon Linting Check
        if not clean_line.startswith(('', '//', '/*', '*')):
            if not clean_line.endswith((';', '{', '}', ',', ':')) and not clean_line.startswith(('if', 'for', 'while', 'switch')):
                stripped_line = text.rstrip()
                if len(stripped_line) > 0:
                    end_idx = len(stripped_line)
                    self.setFormat(end_idx - 1, 1, self.formats["error"])


class ide(QTextEdit):
    def __init__(self, parent=None, state="normal"):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1E1E1E; color: #FFFFFF; selection-background-color: #3A3A3A;")
        self.setFont(QFont("Consolas", 10))
        
        if state == "disabled":
            self.setReadOnly(True)
            
        self.new_file_name = "noname.c"
        
        # Initialize our safe native highlighter attached directly to the document
        self.highlighter = C_SyntaxHighlighter(self.document())


class file(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editors = {}
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.notebook = QTabWidget(self)
        layout.addWidget(self.notebook)
        
        btn_layout = QHBoxLayout()
        self.new_tab = QPushButton("New File", self)
        self.new_tab.clicked.connect(self.add_editor)
        btn_layout.addWidget(self.new_tab)
         
        self.save_btn = QPushButton("Save As (.c)", self)
        self.save_btn.clicked.connect(self.save)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.add_editor()

    def add_editor(self):
        editor = ide(self)
        tab_count = self.notebook.count() + 1
        tab_id = f"Untitled-{tab_count}"
        
        index = self.notebook.addTab(editor, tab_id)
        self.notebook.setCurrentIndex(index)
        self.editors[index] = editor

    def get_current_editor(self):
        current_index = self.notebook.currentIndex()
        return self.editors.get(current_index, None)

    def read(self):
        editor = self.get_current_editor()
        if editor:
            return editor.toPlainText()
        return ""

    def auto_save(self, src_name: str = "noname.c"):
        content = self.read()
        with open(src_name, "w", encoding="utf-8") as f:
            f.write(content)

    def save(self):
        name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "C files (*.c);;All files (*.*)")
        if name:
            content = self.read()
            with open(name, "w", encoding="utf-8") as f:
                f.write(content)
            current_index = self.notebook.currentIndex()
            self.notebook.setTabText(current_index, os.path.basename(name))


class console_log(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1E1E1E; color: #FFFFFF; selection-background-color: #3A3A3A;")
        self.setFont(QFont("Consolas", 10))
        self.setReadOnly(True)

        self.formats = {
            "stdout": QColor("#FFFFFF"),
            "stderr": QColor("#FF5555"),
            "system": QColor("#5DD40E")
        }
        self.console_queue = queue.Queue()

    def write(self, text, tag="stdout"):
        self.moveCursor(QTextCursor.End)
        textColor = self.formats.get(tag, QColor("#FFFFFF"))
        
        fmt = QTextCharFormat()
        fmt.setForeground(textColor)
        self.setCurrentCharFormat(fmt)
        
        self.insertPlainText(text)
        self.ensureCursorVisible()

    def clr_scr(self):
        self.clear()


class MainUI(QWidget):
    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.resize(width, height)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        toolbar_widget = QWidget(self)
        toolbar_widget.setStyleSheet("background-color: #2D2D2D;")
        toolbar_widget.setFixedHeight(40)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        
        btn_style = "background-color: #007acc; color: white; font-family: Consolas; font-size: 13px; font-weight: bold; border: none; padding: 5px 15px;"
        
        self.com_btn = QPushButton("Compile", self)
        self.com_btn.setStyleSheet(btn_style)
        self.com_btn.clicked.connect(self.compile)
        toolbar_layout.addWidget(self.com_btn)

        self.save_file = QPushButton("Save File", self)
        self.save_file.setStyleSheet(btn_style)
        self.save_file.clicked.connect(lambda: self.ide.save())
        toolbar_layout.addWidget(self.save_file)
        
        self.run_btn = QPushButton("Run Compiled", self)
        self.run_btn.setStyleSheet(btn_style)
        self.run_btn.clicked.connect(self.run)
        toolbar_layout.addWidget(self.run_btn)
        toolbar_layout.addStretch()
        
        main_layout.addWidget(toolbar_widget)

        self.splitter = QSplitter(Qt.Vertical, self)
        main_layout.addWidget(self.splitter)
        
        self.ide = file(self.splitter)
        self.splitter.addWidget(self.ide)
        
        self.console = console_log(self.splitter)
        self.splitter.addWidget(self.console)
        
        self.splitter.setSizes([int(height * 0.7), int(height * 0.3)])

        self.compile_timer = QTimer(self)
        self.run_timer = QTimer(self)

    def compile(self):
        self.ide.auto_save()
        os.chdir(os.getcwd())
        current_dir = os.getcwd()
        batch_file = os.path.join(current_dir, "compiler.bat")
        compile_log_file = os.path.join(current_dir, "std_compile_out_err.txt")

        if not os.path.exists(batch_file):
            self.console.clr_scr()
            self.console.write(f"Error: 'compiler.bat' not found in {current_dir}\n", "stderr")
            return

        self.console.clr_scr()
        self.console.write(" Compiling code...\n", "system")

        try:
            open(compile_log_file, "w").close()
            self.compile_log_handle = open(compile_log_file, "w", encoding="utf-8")
        except Exception as e:
            self.console.write(f"❌ Failed to initialize log file: {str(e)}\n", "stderr")
            return

        self.compilation_process = sp.Popen(
            f'cmd /c "{batch_file}"',
            shell=True,
            stdout=self.compile_log_handle,
            stderr=self.compile_log_handle,
            cwd=current_dir,
            creationflags=sp.CREATE_NO_WINDOW,
        )

        self.compile_last_read_position = 0
        self.compile_timer.timeout.connect(lambda: self._tail_compile_log(compile_log_file))
        self.compile_timer.start(50)

    def _tail_compile_log(self, log_file_path):
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8") as f:
                    f.seek(self.compile_last_read_position)
                    new_data = f.read()
                    self.compile_last_read_position = f.tell()
                if new_data:
                    self.console.write(new_data, "stdout")
        except Exception as e:
            print(f"Compilation log tailing error: {e}")

        if self.compilation_process.poll() is not None:
            self.compile_timer.stop()
            self.compile_timer.disconnect()
            
            if hasattr(self, 'compile_log_handle') and not self.compile_log_handle.closed:
                self.compile_log_handle.close()
            
            current_dir = os.getcwd()
            exe_file = os.path.join(current_dir, "noname.exe")
            if os.path.exists(exe_file) and os.path.getsize(exe_file) > 0:
                self.console.write("Compilation finished successfully!\n", "system")
            else:
                self.console.write("Compilation failed. Check syntax errors above.\n", "stderr")

    def run(self):
        self.console.clr_scr()
        self.console.write(" Running program...\n", "system")

        current_dir = os.getcwd()
        run_log_file = os.path.join(current_dir, "std_out_err.txt")

        try:
            open(run_log_file, "w").close()
            self.run_log_handle = open(run_log_file, "w", encoding="utf-8")
        except Exception as e:
            self.console.write(f"❌ Failed to initialize log file: {str(e)}\n", "stderr")
            return

        self.running_process = sp.Popen(
            ["start", "cmd", "/K", "noname.exe"], 
            shell=True,
            cwd=current_dir
        )
        self.run_last_read_position = 0
        self.run_timer.timeout.connect(lambda: self._tail_run_log(run_log_file))
        self.run_timer.start(50)

    def _tail_run_log(self, log_file_path):
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8") as f:
                    f.seek(self.run_last_read_position)
                    new_data = f.read()
                    self.run_last_read_position = f.tell()
                if new_data:
                    self.console.write(new_data, "stdout")
        except Exception as e:
            print(f"Runtime log tailing error: {e}")

        exit_code = self.running_process.poll()

        if exit_code is not None:
            self.run_timer.stop()
            self.run_timer.disconnect()
            
            if hasattr(self, 'run_log_handle') and not self.run_log_handle.closed:
                self.run_log_handle.close()
            
            try:
                if os.path.exists(log_file_path):
                    with open(log_file_path, "r", encoding="utf-8") as f:
                        f.seek(self.run_last_read_position)
                        final_data = f.read()
                        if final_data:
                            self.console.write(final_data, "stdout")
            except Exception:
                pass

            if exit_code == 0:
                self.console.write("\nProgram is done with exit code 0\n", "system")
            else:
                self.console.write(f"\nProgram exited with code: {exit_code}\n", "stderr")  