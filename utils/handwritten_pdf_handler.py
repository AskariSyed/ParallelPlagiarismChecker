import os
import fitz 
from PIL import Image
import pytesseract
import io

def extract_handwritten_text_from_pdf(pdf_path):
    try:
        text = ""
        pdf = fitz.open(pdf_path)
        for page_num in range(len(pdf)):
            page = pdf.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            text += pytesseract.image_to_string(image, lang='eng') + "\n"
        return text
    except Exception as e:
        print(f"Error processing handwritten PDF {pdf_path}: {e}")
        return ""

def handle_handwritten_pdf(file_path, output_dir="data/preprocessed"):
    content = extract_handwritten_text_from_pdf(file_path)
    if not content.strip():
        print(f"No handwritten content extracted from {file_path}")
        return None
    relative_path = os.path.relpath(file_path, os.path.join('data', 'uploads'))
    student_folder = os.path.dirname(relative_path)
    base_name = os.path.basename(file_path) + ".txt"
    out_path = os.path.join(output_dir, student_folder, base_name)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content.lower().strip())
    return (file_path, out_path)