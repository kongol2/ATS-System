import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QVBoxLayout,
    QLineEdit, QPushButton, QFileDialog
)
from parser import ResumeParser
from ner import analyse_resume

class OutputFolder:
    output_folder_path = ""

class ResumeFilterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demands")
        self.resize(200, 400)

        self.experience = ''
        self.specialization = ''
        self.english_level = ''
        self.education_level = ''
        self.additional_info = ''

        # Досвід
        self.experience_label = QLabel("Experience(years):")
        self.experience_combo = QComboBox()
        self.experience_combo.addItems(["Any", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])

        # Спеціалізація
        self.specialization_label = QLabel("Profession:")
        self.specialization_combo = QComboBox()
        self.specialization_combo.addItems(["Any", "Python Developer", "Data Scientist", "Project Manager", "QA Engineer"])

        # Англійська
        self.english_label = QLabel("English requirement:")
        self.english_combo = QComboBox()
        self.english_combo.addItems(["Required", "Not Required"])

        # Освіта
        self.education_label = QLabel("Education level:")
        self.education_combo = QComboBox()
        self.education_combo.addItems(["Any", "Secondary Education", "Vocational Education", "Higher Education", "Graduate Degree"])

        # Додаткова інформація
        self.additional_label = QLabel("Skills:")
        self.additional_input = QLineEdit()

        # Статус
        self.status_label = QLabel("")  # тут буде "Processing..."
        self.status_label.setStyleSheet("color: gray; font-style: italic")

        # Кнопка збереження
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_data)

        # Розміщення віджетів
        layout = QVBoxLayout()
        layout.addWidget(self.experience_label)
        layout.addWidget(self.experience_combo)
        layout.addWidget(self.specialization_label)
        layout.addWidget(self.specialization_combo)
        layout.addWidget(self.english_label)
        layout.addWidget(self.english_combo)
        layout.addWidget(self.education_label)
        layout.addWidget(self.education_combo)
        layout.addWidget(self.additional_label)
        layout.addWidget(self.additional_input)
        layout.addWidget(self.status_label)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_data(self):
        self.status_label.setText("Processing...")
        self.save_button.setEnabled(False)  # Блокуємо кнопку

        # Виконуємо через 1 секунду
        QTimer.singleShot(1000, self.process_data)

    def process_data(self):
        self.experience = "Any" if self.experience_combo.currentText() == "Any" else int(self.experience_combo.currentText())
        self.specialization = self.specialization_combo.currentText()
        self.english_level = True if self.english_combo.currentText() == "Required" else False
        self.education_level = self.education_combo.currentText()
        self.additional_info = set(self.additional_input.text().split(", "))

        print("Saved data:")
        print(f"Experience: {self.experience}")
        print(f"Profession: {self.specialization}")
        print(f"English: {self.english_level}")
        print(f"Education: {self.education_level}")
        print(f"Skills: {self.additional_info}")

        '''if self.education_level == "No higher education":
            print("You need to study more")'''

        analyse_resume(OutputFolder.output_folder_path, self.experience, self.english_level, self.additional_info, self.specialization, self.education_level)

        self.status_label.setText("Done.")
        self.save_button.setEnabled(True)


class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome")
        self.resize(300, 250)
        self.folder_path = ""
        self.label = QLabel("Welcome to Resume Filter!", self)

        self.selection = QLabel("No folder selected")
        self.button_to_select = QPushButton("Select Folder")

        self.button_to_select.clicked.connect(self.select_folder)

        self.button = QPushButton("Start", self)
        self.button.clicked.connect(self.open_main_app)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.selection)
        layout.addWidget(self.button_to_select)
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.main_window = None

    def select_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        OutputFolder.output_folder_path = ResumeParser(self.folder_path).convert_all_files()
        print(f"Output folder path: {OutputFolder.output_folder_path}")
        if self.folder_path:
            self.selection.setText(f"Selected: {self.folder_path}")
            # You can also save it to a variable or use it elsewhere
        print("Full path:", self.folder_path)

    def open_main_app(self):
        self.main_window = ResumeFilterApp()
        self.main_window.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    welcome = WelcomeWindow()
    welcome.show()
    sys.exit(app.exec())