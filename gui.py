import sys
import requests
from PyQt6.QtWidgets import QApplication, QWidget, QTextEdit, QPushButton, QVBoxLayout, QMenu
from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor, QCursor, QAction, QTextDocument
from PyQt6.QtCore import QMimeData, Qt, QThread, pyqtSignal

BACKEND_URL = "http://127.0.0.1:8000"


class CustomTextEdit(QTextEdit):
    """ Custom QTextEdit that enables word selection via right-click """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_words = set()  # Store manually selected words
        self.sensitive_data_cands = set()

    def contextMenuEvent(self, event):
        """ Show a custom right-click menu for selecting/unselecting words """
        cursor = self.textCursor()
        if cursor.hasSelection():
            # If user has selected text, use that instead of word under cursor
            word = cursor.selectedText().strip()
        else:
            # Get cursor position and find the word under the cursor
            cursor = self.cursorForPosition(event.pos())
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText().strip()

        if not word:
            return  # Ignore empty selections

        menu = QMenu(self)
        if word in self.selected_words:
            action_text = "Unselect"
        else:
            action_text = "Select"

        action = QAction(action_text, self)
        action.triggered.connect(lambda: self.toggle_word_selection(word))
        menu.addAction(action)
        menu.exec(event.globalPos())  # Show menu at mouse position

    def toggle_word_selection(self, word):
        """ Toggle word selection (highlight/unhighlight) """
        if word in self.selected_words:
            self.selected_words.remove(word)
            self.highlight_word(word, remove=True)
        elif word in self.sensitive_data_cands:
            self.sensitive_data_cands.remove(word)
            self.highlight_word(word, remove=True)
        else:
            self.selected_words.add(word)
            self.highlight_word(word, remove=False)

    def add_sensitive_cand(self, cand):
        if cand not in self.sensitive_data_cands and cand not in self.selected_words:
            self.sensitive_data_cands.add(cand)
            self.highlight_word(cand, color=QColor(255, 69, 0))

    def highlight_word(self, word, remove=False, color=QColor(0, 128, 255)):
        """ Highlight or unhighlight a word """
        cursor = self.textCursor()
        doc = self.document()

        word_format = QTextCharFormat()
        if remove:
            word_format.setForeground(QColor(255, 255, 255))  # Reset to white
            word_format.setFontWeight(QFont.Weight.Normal)
        else:
            word_format.setForeground(color)  # Blue for user-selected words
            word_format.setFontWeight(QFont.Weight.Bold)

        cursor.movePosition(QTextCursor.MoveOperation.Start)

        while True:
            cursor = doc.find(word, cursor, QTextDocument.FindFlag.FindCaseSensitively)
            if cursor.isNull():
                break
            cursor.mergeCharFormat(word_format)

    def insertFromMimeData(self, source: QMimeData):
        """ Forces plain text pasting and enables word wrap """
        if source.hasText():
            self.insertPlainText(source.text())

    def get_sensitive_cands(self):
        return list(self.selected_words) + list(self.sensitive_data_cands)

    def replace_placeholders(self, placeholders: dict):
        """ Replace placeholders in the text field with corresponding values and highlight them """
        cursor = self.textCursor()
        doc = self.document()

        cursor.movePosition(QTextCursor.MoveOperation.Start)

        for placeholder, replacement in placeholders.items():
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            while True:
                cursor = doc.find(placeholder, cursor, QTextDocument.FindFlag.FindCaseSensitively)
                if cursor.isNull():
                    break
                cursor.insertText(replacement)
                self.highlight_word(replacement, color=QColor(255, 69, 0))  # Highlight replaced words


class APICallThread(QThread):
    result_ready_list = pyqtSignal(list)  # Signal for list results
    result_ready_dict = pyqtSignal(dict)  # Signal for dict results

    def __init__(self, name, args, response_field, default_val):
        super().__init__()
        self.name = name
        self.args = args
        self.response_field = response_field
        self.default_val = default_val

        # Determine the correct signal type to use
        self.result_ready = self.result_ready_list if isinstance(default_val, list) else self.result_ready_dict

    def run(self):
        response = requests.post(f"{BACKEND_URL}/{self.name}", json=self.args)
        if response.status_code == 200:
            response_data = response.json().get(f"{self.response_field}", self.default_val)
            self.result_ready.emit(response_data)


class SensitiveInfoApp(QWidget):
    def __init__(self):
        super().__init__()

        self.place_holder_thread = None
        self.detect_thread = None
        self.text_edit = CustomTextEdit(self)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # Prevent horizontal scrolling
        self.process_button = QPushButton("Detect Sensitive Info", self)
        self.replace_button = QPushButton("Replace with Placeholders", self)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.process_button)
        layout.addWidget(self.replace_button)
        self.setLayout(layout)

        self.process_button.clicked.connect(self.detect_sensitive_info)
        self.replace_button.clicked.connect(self.replace_sensitive_info)

        self.setWindowTitle("Sensitive Info Selector")
        self.resize(600, 400)
        self.showMaximized()
        self.sensitive_words = []

    def detect_sensitive_info(self):
        """ Run detection in a separate thread with a loading animation """
        text = self.text_edit.toPlainText()

        # Disable button & show loading cursor
        self.process_button.setEnabled(False)
        self.replace_button.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        # Start background processing
        self.detect_thread = APICallThread("detect", {"text": text}, "sensitive_words", [])
        print(self.detect_thread.result_ready)
        self.detect_thread.result_ready.connect(self.on_detection_complete)
        self.detect_thread.start()

    def on_detection_complete(self, sensitive_words):
        """ Handle the result and restore UI """
        for word in sensitive_words:
            self.text_edit.add_sensitive_cand(word)

        print(sensitive_words)

        # Restore button & cursor
        self.process_button.setEnabled(True)
        self.replace_button.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def on_place_holder_complete(self, place_holders: dict):
        """ Handle the result and restore UI """

        print("place_holders: ", place_holders)

        self.text_edit.replace_placeholders(place_holders)

        # Restore button & cursor
        self.process_button.setEnabled(True)
        self.replace_button.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def replace_sensitive_info(self):
        """ Send text to backend and replace sensitive words with placeholders """
        # Disable button & show loading cursor
        self.process_button.setEnabled(False)
        self.replace_button.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        # Start background processing
        args = {'text': ', '.join(self.text_edit.get_sensitive_cands())}
        self.place_holder_thread = APICallThread("place_holder", args, "place_holders", {})
        self.place_holder_thread.result_ready.connect(self.on_place_holder_complete)
        self.place_holder_thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SensitiveInfoApp()
    window.show()
    sys.exit(app.exec())
