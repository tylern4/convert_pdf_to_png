import json
import subprocess
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QWidget,
)
from wand.image import Image


def convert(filename: str):
    file_name = Path(filename)
    new_parent = Path(file_name.as_posix()[:-4])
    new_parent.mkdir(exist_ok=True, parents=True)
    subprocess.call(
        [
            "magick",
            "convert",
            "-density",
            "192",
            file_name.as_posix(),
            f"{new_parent.as_posix()}/{file_name.name[:-4]}.png",
        ]
    )


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        settings_file = Path().home() / ".config" / "pdf_to_png" / "settings.json"
        if settings_file.exists():
            self.settings = json.loads(settings_file.read_text())
        else:
            self.settings = {"directory": Path.cwd().as_posix()}

        self.setWindowTitle("Convert PDF to PNG")
        self.setGeometry(100, 100, 400, 100)

        self.layout = QGridLayout()

        # file selection
        self.file_browse = QPushButton("Browse")

        self.filename_edit = QLineEdit()

        self.layout.addWidget(QLabel("File:"), 0, 0)
        self.layout.addWidget(self.filename_edit, 0, 1)
        self.layout.addWidget(self.file_browse, 0, 2)
        self.file_browse.clicked.connect(self.open_file_dialog)

        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)  # Initial value

        self.startButton = QPushButton("Start Progress")
        self.startButton.clicked.connect(self.start_progress)

        self.layout.addWidget(self.progressBar)
        self.layout.addWidget(self.startButton)
        self.setLayout(self.layout)

        self.timer = QTimer(self)

        self.show()

    def start_progress(self):
        self.progress_value = 0
        self.progressBar.setValue(0)
        self.timer.start(50)

    def update_progress(self):
        self.progress_value += 1
        self.progressBar.setValue(self.progress_value)
        if self.progress_value >= 100:
            self.timer.stop()

    def open_file_dialog(self):
        filename, ok = QFileDialog.getOpenFileName(
            self,
            "Select a File",
            self.settings["directory"],
            "pdfs (*.pdf *.PDF)",
        )
        self.filename = filename
        self.start_progress()
        self.start_convert()

    def start_convert(self):
        file_name = Path(self.filename)
        new_parent = Path(file_name.as_posix()[:-4])
        new_parent.mkdir(exist_ok=True, parents=True)

        with Image(filename=self.filename) as full_pdf:
            num_pages = len(full_pdf.sequence)
            self.progressBar.setRange(0, num_pages)
            self.progressBar.setValue(0)  # Initial value
            for page_num in range(num_pages):
                self.update_progress()
                with full_pdf.sequence[page_num] as frame:
                    page = Image(frame)
                    print(
                        f"{new_parent.as_posix()}/{file_name.name[:-4]}.{page_num:04d}.png"
                    )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
