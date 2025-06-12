import os
from datetime import datetime, timezone
import PyPDF2 as pdf
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

'''користувач вказує шлях до папки з резюме а програма повертає шлях до папки з уже готовими текстовими файлами
прописати витягнення з докс файлу
закинути на гітхаб результат і об'єднати між собою інтерфейс та реалізацію'''
class ResumeParser:

    def __init__(self, folder_path):
        self.folder_path = folder_path
        utc_now = datetime.now(timezone.utc)
        formatted = utc_now.strftime("%H_%M_%d_%m_%Y")
        self.output_folder = "txts_" + formatted
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def iter_block_items(self, parent):
        for child in parent.element.body.iterchildren():
            if child.tag.endswith('}p'):
                yield Paragraph(child, parent)
            elif child.tag.endswith('}tbl'):
                yield Table(child, parent)

    def extract_from_docx(self, file_path):
        doc = Document(file_path)
        full_content = []
        for block in self.iter_block_items(doc):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if text:
                    full_content.append(text)
            elif isinstance(block, Table):
                table_lines = []
                for row in block.rows:
                    row_text = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                    table_lines.append("| " + " | ".join(row_text) + " |")
                if table_lines:
                    header = table_lines[0]
                    divider = "|---" * len(table_lines[0].split("|")[1:-1]) + "|"
                    full_content.append("[Таблиця]\n" + header + "\n" + divider + "\n" + "\n".join(table_lines[1:]))

        return "\n\n".join(full_content)

    def extract_from_pdf(self, file_path):
        text = ""
        try:
            with open(file_path, "rb") as pdf_file:
                reader = pdf.PdfReader(pdf_file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
        except Exception as e:
            print(f"Error reading {file_path} with PyPDF2: {e}")
        return text

    def convert_all_files(self):
        for filename in os.listdir(self.folder_path):
            if filename.lower().endswith(".pdf"):
                full_path = os.path.join(self.folder_path, filename)
                extracted_text = self.extract_from_pdf(full_path)
                self.save_text_file(filename, extracted_text)
            elif filename.lower().endswith(".docx"):
                full_path_docx = os.path.join(self.folder_path, filename)
                extracted_text_docx = self.extract_from_docx(full_path_docx)
                self.save_text_file(filename, extracted_text_docx)
        return self.output_folder

    def save_text_file(self, pdf_filename, content):
        txt_filename = os.path.splitext(pdf_filename)[0] + ".txt"
        txt_path = os.path.join(self.output_folder, txt_filename)
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error writing to {txt_path}: {e}")