import os
import re

def merge_numbered_files(directory):
    # Regular expression to match the number pattern at the end (-\d+.txt)
    number_pattern = re.compile(r'-(\d+)\.txt$')
    
    # Walk through all directories recursively
    for root, dirs, files in os.walk(directory):
        # Dictionary to group files by their base name (without the number suffix)
        file_groups = {}
        
        # Filter and group txt files
        for filename in files:
            if filename.endswith('.txt'):
                match = number_pattern.search(filename)
                if match:
                    # Get the base name by removing the number suffix
                    base_name = filename[:match.start()]
                    if base_name not in file_groups:
                        file_groups[base_name] = []
                    file_groups[base_name].append(filename)
        
        # Process each group of files in current directory
        for base_name, files in file_groups.items():
            if len(files) <= 1:  # Skip if there's only one file or no files
                continue
                
            # Sort files by their number suffix
            sorted_files = sorted(files, key=lambda x: int(number_pattern.search(x).group(1)))
            
            # Create output filename (base name + .txt)
            output_file = base_name + '.txt'
            output_path = os.path.join(root, output_file)
            
            print(f"\nProcessing directory: {root}")
            print(f"Merging files for {base_name}:")
            print(f"Input files: {sorted_files}")
            print(f"Output file: {output_file}")
            
            # Merge files
            try:
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    for file in sorted_files:
                        file_path = os.path.join(root, file)
                        print(f"Processing: {file}")
                        try:
                            # Try different encodings
                            encodings = ['utf-8', 'gbk', 'shift-jis', 'utf-16']
                            content = None
                            
                            for encoding in encodings:
                                try:
                                    with open(file_path, 'r', encoding=encoding) as infile:
                                        content = infile.read()
                                    print(f"Successfully read with {encoding} encoding")
                                    break
                                except UnicodeDecodeError:
                                    continue
                            
                            if content is None:
                                raise Exception("Failed to read file with any supported encoding")
                            
                            outfile.write(content)
                            outfile.write('\n')  # Add newline between files
                            
                            # Optionally, remove the original file after successful merge
                            os.remove(file_path)
                            print(f"Deleted: {file}")
                            
                        except Exception as e:
                            print(f"Error processing {file}: {str(e)}")
                
                print(f"Successfully merged {len(files)} files into {output_file}")
                
            except Exception as e:
                print(f"Error creating output file {output_file}: {str(e)}")

# Example usage
directory = "/root/trans-sexy-novel/tag-R-18/雌堕"  # Replace with your directory path
merge_numbered_files(directory)
