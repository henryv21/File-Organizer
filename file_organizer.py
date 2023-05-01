import os
import shutil
from datetime import datetime
import magic
from PIL import Image
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QPushButton, QTextEdit, QVBoxLayout
from dateutil.parser import parse
import pyheif


# UI setup for the main window
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(400, 300)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.verticalLayout = QVBoxLayout(self.centralwidget)

        self.label = QLabel("Select a folder to organize files based on their types and dates.")
        self.verticalLayout.addWidget(self.label)

        self.browse_button = QPushButton("Browse")
        self.verticalLayout.addWidget(self.browse_button)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.verticalLayout.addWidget(self.status_text)

        MainWindow.setCentralWidget(self.centralwidget)

# Function to sanitize date string and correct the hour value if it's outside the valid range
def sanitize_date_string(date_str):
    date_parts = date_str.split(':')
    if len(date_parts) >= 3:
        hour = int(date_parts[3]) % 24
        date_parts[3] = str(hour)
    return ':'.join(date_parts)


# FileOrganizer class inherits QMainWindow and Ui_MainWindow
class FileOrganizer(QMainWindow, Ui_MainWindow):
    def __init__(self):
        print("Initializing FileOrganizer...")
        super().__init__()
        self.setupUi(self)
        self.browse_button.clicked.connect(self.browse_folder)

    # Function called when the browse button is clicked
    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select a folder")
        self.organize_files(folder_path)

    # Function to organize files in the specified folder
    def organize_files(self, folder_path):
        self.status_text.clear()
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_type = magic.from_file(file_path, mime=True)

                # Determine the category based on file type
                if file_type.startswith('image/'):
                    category = 'Images'
                elif file_type.startswith('video/'):
                    category = 'Videos'
                elif file_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                    category = 'Documents'
                else:
                    continue

                # Get the date folder for the file
                date_folder = self.get_file_date_folder(file_path, file_type)
                dest_folder = os.path.join(folder_path, category, date_folder)

                # Create destination folder if it doesn't exist and move the file
                os.makedirs(dest_folder, exist_ok=True)
                shutil.move(file_path, os.path.join(dest_folder, file))
                self.status_text.append(f'Moved {file_path} to {os.path.join(dest_folder, file)}')

    # Function to get the date folder based on file metadata or modified date
    def get_file_date_folder(self, file_path, file_type):
        if file_type.startswith('image/'):
            if file_type == 'image/heif':
                try:
                    heif_file = pyheif.read(file_path)
                    exif_data = {entry['tag']: entry['value'] for entry in heif_file.metadata or [] if entry['type'] == 'Exif'}
                    date_str = exif_data.get(36867)
                except Exception:
                    date_str = None
            else:
                try:
                    with Image.open(file_path) as img:
                        exif_data = img._getexif()
                        date_str = exif_data.get(36867) if exif_data else None
                except Exception:
                    date_str = None
        elif file_type.startswith('video/'):
            date_str = None
        else:
            date_str = None

        if date_str:
            date_str = sanitize_date_string(date_str)
            date_obj = parse(date_str)
        else:
            date_obj = datetime.fromtimestamp(os.path.getmtime(file_path))

        date_folder = date_obj.strftime('%Y/%B')
        return date_folder


if __name__ == "__main__":
    print("Starting the app...")
    app = QApplication([])
    window = FileOrganizer()
    window.show()
    app.exec_()
