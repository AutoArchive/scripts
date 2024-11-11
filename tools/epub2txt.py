import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
from pathlib import Path

def epub_to_text(epub_path):
    """Convert a single epub file to text"""
    print(f"Starting conversion of {epub_path}")
    book = epub.read_epub(epub_path)
    chapters = []
    
    print(f"Found {len(list(book.get_items()))} items in epub")
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            print(f"Processing document item: {item.get_name()}")
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text()
            print(f"Extracted text length: {len(text)}")
            chapters.append(text)
    
    print(f"Total chapters processed: {len(chapters)}")
    return '\n\n'.join(chapters)

def combine_epubs_to_txt(input_dir, output_file):
    """Convert all epubs in a directory to a single txt file"""
    # Get all epub files in the directory
    epub_files = sorted([f for f in Path(input_dir).glob('*.epub')])
    print(f"Found {len(epub_files)} epub files in directory")
    
    all_text = []
    
    # Process each epub file
    for epub_file in epub_files:
        print(f"\nProcessing: {epub_file.name}")
        try:
            text = epub_to_text(str(epub_file))
            print(f"Extracted text length: {len(text)}")
            # Add file name as separator
            all_text.append(f"\n\n{'='*50}\n{epub_file.name}\n{'='*50}\n\n")
            all_text.append(text)
        except Exception as e:
            print(f"Error processing {epub_file.name}: {str(e)}")
    
    print(f"\nTotal texts collected: {len(all_text)}")
    
    # Write all text to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_text))
    
    print(f"Conversion complete. Output saved to: {output_file}")

# Usage
input_directory = "/root/trans-cn-digital/文学作品和艺术创作/小说/《银荆的告白》1-5卷"
output_file = "/root/trans-cn-digital/文学作品和艺术创作/小说/银荆的告白_全卷.txt"

combine_epubs_to_txt(input_directory, output_file)
