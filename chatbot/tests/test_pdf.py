# Code for testing PDF text extraction using PyPDF2, PyMuPDF, and PDFMiner
# Assumes that the PDF files are stored in a directory "./test_pdfs"


import os
import PyPDF2
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract
from spellchecker import SpellChecker
import time

# Initialize spell checker
spell = SpellChecker()

def calculate_spelling_accuracy(text):
    words = text.split()
    if not words:
        return 0
    misspelled = spell.unknown(words)
    correctly_spelled = len(words) - len(misspelled)
    return (correctly_spelled / len(words)) * 100

def extract_text_pypdf2(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text.strip()
    except Exception as e:
        return f"Error using PyPDF2: {e}"

def extract_text_pymupdf(pdf_path):
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
            return text.strip()
    except Exception as e:
        return f"Error using PyMuPDF: {e}"

def extract_text_pdfminer(pdf_path):
    try:
        text = pdfminer_extract(pdf_path)
        return text.strip()
    except Exception as e:
        return f"Error using PDFMiner: {e}"

def process_pdfs(pdf_dir, output_file):
    extractors = {
        "PyPDF2": extract_text_pypdf2,
        "PyMuPDF": extract_text_pymupdf,
        "PDFMiner": extract_text_pdfminer
    }
    
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    # Create results directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("PDF Text Extraction Summary\n")
        f.write("========================\n\n")
        
        # Process each extractor separately
        for extractor_name, extractor_func in extractors.items():
            total_start_time = time.time()
            total_words = 0
            total_spelling_accuracy = 0
            successful_files = 0
            
            f.write(f"{extractor_name} Results:\n")
            f.write("-----------------\n")
            
            # Process all PDFs with current extractor
            for pdf_file in pdf_files:
                pdf_path = os.path.join(pdf_dir, pdf_file)
                text = extractor_func(pdf_path)
                
                if not text.startswith("Error"):
                    words = text.split()
                    total_words += len(words)
                    accuracy = calculate_spelling_accuracy(text)
                    total_spelling_accuracy += accuracy
                    successful_files += 1
            
            total_time = time.time() - total_start_time
            avg_spelling_accuracy = total_spelling_accuracy / successful_files if successful_files > 0 else 0
            
            f.write(f"Total Words Detected: {total_words:,}\n")
            f.write(f"Average Spelling Accuracy: {avg_spelling_accuracy:.2f}%\n")
            f.write(f"Total Processing Time: {total_time:.2f} seconds\n")

# Directories and paths
pdf_directory = "./test_pdfs"
output_file = "./results/all_pdf_stats.txt"

# Process PDFs and generate condensed summary
process_pdfs(pdf_directory, output_file)