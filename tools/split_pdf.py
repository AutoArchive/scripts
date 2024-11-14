import os
import argparse
from PyPDF2 import PdfReader, PdfWriter

def get_pdf_size_mb(file_path):
    """Return the size of PDF file in megabytes"""
    return os.path.getsize(file_path) / (1024 * 1024)

def split_pdf(input_path, output_dir=None, max_size_mb=20):
    """
    Split a PDF file into multiple files if it exceeds the maximum size.
    
    Args:
        input_path (str): Path to the input PDF file
        output_dir (str): Directory to save split files (default: same as input file)
        max_size_mb (int): Maximum size for each split file in MB (default: 25)
    """
    if get_pdf_size_mb(input_path) <= 50:
        print(f"PDF is smaller than 50MB. No splitting needed.")
        return

    # Set output directory to input file's directory if not specified
    if output_dir is None:
        output_dir = os.path.dirname(input_path) or '.'
    os.makedirs(output_dir, exist_ok=True)

    # Read the PDF
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    
    # Initialize variables
    current_writer = PdfWriter()
    current_pages = 0
    part = 1
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    for page_num in range(total_pages):
        current_writer.add_page(reader.pages[page_num])
        current_pages += 1
        
        # Create temporary file to check size
        temp_output = os.path.join(output_dir, f"{base_name}_temp.pdf")
        with open(temp_output, 'wb') as temp_file:
            current_writer.write(temp_file)
        
        # Check if current split file exceeds max size
        if get_pdf_size_mb(temp_output) >= max_size_mb:
            # Save current split and start new one
            output_path = os.path.join(output_dir, f"{base_name}_part{part}.pdf")
            with open(output_path, 'wb') as output_file:
                current_writer.write(output_file)
            
            print(f"Created {output_path}")
            
            # Reset for next split
            current_writer = PdfWriter()
            current_writer.add_page(reader.pages[page_num])  # Add current page to new split
            part += 1
        
        os.remove(temp_output)  # Clean up temporary file
    
    # Save the last part if it contains any pages
    if current_writer.pages:
        output_path = os.path.join(output_dir, f"{base_name}_part{part}.pdf")
        with open(output_path, 'wb') as output_file:
            current_writer.write(output_file)
        print(f"Created {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Split large PDF files into smaller parts')
    parser.add_argument('input_pdf', help='Path to the input PDF file')
    parser.add_argument('-o', '--output-dir', help='Output directory (default: same as input file)')
    parser.add_argument('-s', '--max-size', type=int, default=20,
                        help='Maximum size for each split file in MB (default: 25)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_pdf):
        print(f"Error: File '{args.input_pdf}' not found!")
        return 1
        
    split_pdf(args.input_pdf, args.output_dir, args.max_size)
    return 0

if __name__ == "__main__":
    exit(main())
