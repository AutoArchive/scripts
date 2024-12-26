import os
import subprocess
import re
import yaml
import argparse

def convert_doc_to_text(filepath):
    """Convert doc/docx to text, with error handling"""
    try:
        if filepath.endswith('.docx'):
            result = subprocess.run(['pandoc', '-f', 'docx', '-t', 'markdown', filepath], 
                                  capture_output=True, text=True, check=True)
            return result.stdout
        elif filepath.endswith('.doc'):
            result = subprocess.run(['antiword', filepath], 
                                  capture_output=True, text=True, check=True)
            return result.stdout
        elif filepath.endswith('.txt'):
            with open(filepath, 'r') as file:
                return file.read()
    except subprocess.CalledProcessError as e:
        print(f"Error converting {filepath}: {e}")
    except Exception as e:
        print(f"Unexpected error converting {filepath}: {e}")
    return None

def get_file_mapping_from_config(config_path):
    """Read config.yml and return filename->page mapping"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    mapping = {}
    if 'files' in config:
        for file in config.get('files', []):
            if 'filename' in file and 'page' in file:
                mapping[file['filename']] = file['page']
    return mapping

SPECIAL_CHARS = r"""
        \s          # spaces and whitespace
        \d          # digits
        a-zA-Z      # letters
        \~\`        # tildes and backticks
        \!\@\#\$   # common special chars
        \%\^\&\*   # more special chars
        \(\)\[\]   # brackets
        \{\}\<\>   # angle brackets
        \-\_\+\=   # math symbols
        \|\\\/'    # slashes and vertical bar
        \"\;\:\,   # punctuation
        \.\?・      # dots and question marks
    """

def is_control_sequence_line(line):
    """Check if line contains only control characters"""
    # All possible special chars and patterns
    pattern = f"^[{SPECIAL_CHARS.replace(' ','').replace('#.*\n','')}]*$"
    
    has_only_controls = bool(re.match(pattern, line, re.VERBOSE))
    has_required_chars = bool(re.search(r'[\d\~\^\?\:\)\!\@\#\$\%\^\&\*\(\)\[\]\{\}\<\>\_\+\-\=\|\\\/\'\"\`\;\,]', line))
    no_chinese = not bool(re.search(r'[\u4e00-\u9fff]', line))
    
    return has_only_controls and has_required_chars and no_chinese

def strip_trailing_special_chars(line):
    """Strip special characters from end of line if there are 8+ consecutive special chars"""
    pattern = f"[{SPECIAL_CHARS.replace(' ','').replace('#.*\n','')}]{{8,}}$"
    return re.sub(pattern, '', line, flags=re.VERBOSE)

def clean_control_sequences(text):
    """Clean control sequences and special markers from text"""
    
    text = re.sub(r'\\*\s*\[*\.?24小时在线客服\.*\]*', '', text)
    text = re.sub(r'\\*\s*\[*\.?唯一联系方式\.*\]*', '', text)
    text = re.sub(r'\\*\s*\[*\.?646208907\.*\]*', '', text)
    text = re.sub(r'\\*\s*\[*\.?2775269676\.*\]*', '', text)
    text = re.sub(r'\\*\s*\[*\.?终身免费更\.*\]*', '', text)
    text = re.sub(r'\\*\s*\[*\.?更全小说等\.*\]*', '', text)
    text = re.sub(r'\\*\s*\[*\.?缺失章节等\.*\]*', '', text)
    text = re.sub(r'\\*\s*\[*\.?一次购买\.*\]*', '', text)
    text = re.sub(r'\\*\s*\[*\.?以及备用QQ\.*\]*', '', text)
    text = re.sub(r'\\*\s*\[*\.?漫画视频账号\.*\]*', '', text)
    
    # Split into lines
    lines = text.split('\n')
    # Filter out control sequence lines
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not is_control_sequence_line(stripped):
            # Add new function call here
            stripped = strip_trailing_special_chars(stripped)
            cleaned_lines.append(stripped)
    
    # Join remaining lines
    text = '\n'.join(cleaned_lines)
    
    # Remove common advertising markers
    
    # Clean remaining control sequences
    text = re.sub(r'\\+\s*', ' ', text)
    text = re.sub(r'\\([^\\])', r'\1', text)
    text = text.replace('\\', '')
    # convert the single '\n' to double for markdown.
    text = text.replace('\n', '\n\n')
    return text.strip()


def process_page_file(filepath, file_mapping, base_dir, remove_original):
    """Process single markdown page file using config mapping"""
    print(f"\nProcessing file: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'<!--\s*tcd_download_link\s*-->\n(.*?)\n<!--\s*tcd_download_link_end\s*-->'
        match = re.search(pattern, content, re.DOTALL)

        if "tcd_main_text" in content:
            print("skip because already exists")
            return
        
        if not match:
            print(f"No download link found in: {filepath}")
            return
        
        download_text = match.group(1).strip()
        print(f"Found download text: {download_text}")
        
        doc_filename = None
        for filename in file_mapping.keys():
            if file_mapping[filename] == os.path.basename(filepath):
                doc_filename = filename
                break
        
        if not doc_filename:
            doc_filename = re.search(r'\[(.*?)\]', download_text)
            if doc_filename:
                doc_filename = doc_filename.group(1)
        
        if not doc_filename:
            print(f"Could not find matching doc file for: {filepath}")
            return
            
        doc_path = os.path.join(base_dir, doc_filename)
        if not os.path.exists(doc_path):
            print(f"Document not found: {doc_path}")
            return
        
        print(f"Found document at: {doc_path}")
        converted_text = convert_doc_to_text(doc_path)
        if not converted_text:
            return
        
        # if file content is > 500KB, add noticce
        def check_text_length_and_add_notice(converted_text):
            if len(converted_text.encode('utf-8')) > 100 * 1024:  # 100KB
                notice = "\n\n文件内容超过上限。请下载txt文件获取完整版。\n"
                converted_text = converted_text[:100 * 1024] + notice
                print("Notice added to the text. Please download the txt file and truncate the content.")
            return converted_text
        if not remove_original:
            converted_text = check_text_length_and_add_notice(converted_text)


        # Clean control sequences instead of escaping
        converted_text = clean_control_sequences(converted_text)
        
        new_section = f'''

## 正文 {{ data-search-exclude }}

<!-- tcd_main_text -->
{converted_text}
<!-- tcd_main_text_end -->

'''
        
        # Use string replacement instead of regex for substitution
        start = content.find('<!-- tcd_download_link -->')
        end = content.find('<!-- tcd_download_link_end -->') + len('<!-- tcd_download_link_end -->')
        if start >= 0 and end >= 0:
            old_file_path = filepath
            if remove_original:
                filepath = filepath.replace("_page.md", ".md")
                new_content = content[:start] + content[end:] + new_section
            else:
                new_content = content + new_section
            new_content = new_content.replace("## 其他信息\n", "## 其他信息 [Processed Page Metadata]\n")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Successfully processed: {filepath}")
            if remove_original:
                os.remove(doc_path)
                os.remove(old_file_path)
        
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Process markdown files.')
    parser.add_argument('--remove-original', default=False, help='Remove the original file and link to the original file')
    args = parser.parse_args()

    for root, dirs, files in os.walk('.'):
        if 'config.yml' in files:
            config_path = os.path.join(root, 'config.yml')
            print(f"\nFound config at: {config_path}")
            
            file_mapping = get_file_mapping_from_config(config_path)
            
            for page_file in [f for f in files if f.endswith('_page.md')]:
                page_path = os.path.join(root, page_file)
                process_page_file(page_path, file_mapping, root, args.remove_original)

if __name__ == '__main__':
    main()
