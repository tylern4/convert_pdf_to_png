import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)
from wand.image import Image


def process_pdf_page(in_filename, page_num, out_filename):
    with Image(filename=f"{in_filename}[{page_num}]", resolution=500) as frame:
        page = Image(frame)
        page.save(
            filename=out_filename,
        )
    return True


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
        self.setLayout(self.layout)

        self.show()

    def open_file_dialog(self):
        filename, ok = QFileDialog.getOpenFileName(
            self,
            "Select a File",
            self.settings["directory"],
            "pdfs (*.pdf *.PDF)",
        )
        self.filename = filename
        self.start_convert()

    def start_convert(self):
        file_name = Path(self.filename)
        new_parent = Path(file_name.as_posix()[:-4])
        new_parent.mkdir(exist_ok=True, parents=True)

        with Image(filename=self.filename) as full_pdf:
            self.num_pages = len(full_pdf.sequence)
        threads = []
        with ThreadPoolExecutor(max_workers=12) as exe:
            for page_num in range(self.num_pages):
                out_filename = (
                    f"{new_parent.as_posix()}/{file_name.name[:-4]}.{page_num:04d}.png"
                )
                threads.append(
                    exe.submit(process_pdf_page, self.filename, page_num, out_filename)
                )

        [t.result() for t in as_completed(threads)]
        exit(0)


def main():
    app = QApplication(sys.argv)
    _window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
