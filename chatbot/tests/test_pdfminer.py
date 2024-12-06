# Code for testing PDF text cleaning with PDFMiner
# Assumes that the PDF text files have already been extracted using PDFMiner and saved in a directory "./test_pdf_outputs"

import os
import glob
import tiktoken

# Initialize tokenizer
encoding = tiktoken.encoding_for_model("gpt-4o-mini-2024-07-18")

def count_tokens(text):
    """Count tokens in text using tiktoken, allowing endoftext token"""
    return len(encoding.encode(text, allowed_special={'<|endoftext|>'}, disallowed_special=()))

def process_text_files(directory, output_file):
    # Create results directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Get all text files with PDFMiner in the name
    files = glob.glob(os.path.join(directory, "*PDFMiner.txt"))
    
    total_tokens_before = 0
    total_tokens_after = 0
    decreases = []
    
    # Open file for writing results
    with open(output_file, 'w', encoding='utf-8') as out_file:
        out_file.write(f"PDFMiner Text Extraction Analysis\n")
        out_file.write("=" * 50 + "\n\n")
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Skip the stats header (first 5 lines)
                    for _ in range(5):
                        next(f)
                    text = f.read()
                
                # Count tokens before cleaning
                tokens_before = count_tokens(text)
                
                # Clean text
                cleaned_text = text.replace('\n', ' ').replace('  ', ' ')
                
                # Count tokens after cleaning
                tokens_after = count_tokens(cleaned_text)
                
                # Calculate decrease percentage
                decrease_percent = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0
                
                # Add to totals
                total_tokens_before += tokens_before
                total_tokens_after += tokens_after
                decreases.append(decrease_percent)
            
            except Exception as e:
                out_file.write(f"Error processing file: {file_path}\n")
                out_file.write(f"Error: {str(e)}\n")
        
        # Calculate and write aggregate results
        avg_decrease = sum(decreases) / len(decreases) if decreases else 0
        
        out_file.write(f"Total tokens before cleaning (all documents): {total_tokens_before:,}\n")
        out_file.write(f"Total tokens after cleaning (all documents): {total_tokens_after:,}\n")
        out_file.write(f"Average token decrease percentage: {avg_decrease:.2f}%\n")
        out_file.write(f"Total number of documents processed: {len(files)}\n")

# Process files and write results
process_text_files('./test_pdf_outputs', './results/cleaning_extraction.txt')