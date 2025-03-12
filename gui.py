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
        cursor = self.cursorForPosition(event.pos())  # Get cursor position
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


class DetectThread(QThread):
    result_ready = pyqtSignal(list)  # Signal to send detected words

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        response = requests.post(f"{BACKEND_URL}/detect", json={"text": self.text})
        if response.status_code == 200:
            sensitive_words = response.json().get("sensitive_words", [])
            self.result_ready.emit(sensitive_words)


class SensitiveInfoApp(QWidget):
    def __init__(self):
        super().__init__()

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

    def highlight_sensitive_words(self):
        """ Highlight given words in the text edit """
        text = self.text_edit.toPlainText()
        cursor = self.text_edit.textCursor()
        doc = self.text_edit.document()  # Get document reference

        format = QTextCharFormat()
        format.setForeground(QColor(255, 69, 0))  # Orange-Red color
        format.setFontWeight(QFont.Weight.Bold)

        # Reset formatting before applying new highlights
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())

        for word in self.sensitive_words:
            cursor = doc.find(word)  # Use QTextDocument.find()
            while not cursor.isNull():  # If found, apply formatting
                cursor.mergeCharFormat(format)
                cursor = doc.find(word, cursor)  # Find next occurrence

    def detect_sensitive_info(self):
        """ Run detection in a separate thread with a loading animation """
        text = self.text_edit.toPlainText()

        # Disable button & show loading cursor
        self.process_button.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        # Start background processing
        self.thread = DetectThread(text)
        self.thread.result_ready.connect(self.on_detection_complete)
        self.thread.start()

    def on_detection_complete(self, sensitive_words):
        """ Handle the result and restore UI """
        for word in sensitive_words:
            self.text_edit.add_sensitive_cand(word)

        print(sensitive_words)

        # Restore button & cursor
        self.process_button.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def replace_sensitive_info(self):
        """ Send text to backend and replace sensitive words with placeholders """
        text = self.text_edit.toPlainText()
        response = requests.post(f"{BACKEND_URL}/replace", json={"sensitive_words": self.sensitive_words})
        if response.status_code == 200:
            anonymized_text = response.json()["anonymized_text"]
            self.text_edit.setText(anonymized_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SensitiveInfoApp()
    window.show()
    sys.exit(app.exec())
