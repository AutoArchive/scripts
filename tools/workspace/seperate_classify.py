import yaml
import os
import shutil

def organize_files():
    # Create directories if they don't exist
    workspace_dir = "workspace"
    unrelated_dir = "unrelated_workspace"
    
    for directory in [workspace_dir, unrelated_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Read and parse the YAML file
    with open('.github/evaluated.yml', 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    # Process each file
    for filename, info in data.items():
        # Skip if the score isn't present
        if 'relevance_score' not in info:
            continue
        
        score = info['relevance_score']
        
        # Construct the source path (file is in workspace directory)
        source_path = os.path.join(workspace_dir, filename)
        
        # Skip if file doesn't exist in workspace directory
        if not os.path.exists(source_path):
            continue

        # For files with score <= 2, move to unrelated_workspace
        if score <= 2:
            try:
                # Create necessary subdirectories in unrelated_workspace
                os.makedirs(os.path.dirname(os.path.join(unrelated_dir, filename)), exist_ok=True)
                shutil.move(source_path, os.path.join(unrelated_dir, filename))
                print(f"Moved '{filename}' to {unrelated_dir}/ (Score: {score})")
            except Exception as e:
                print(f"Error moving '{filename}': {str(e)}")
        # Files with score > 2 stay in workspace directory

if __name__ == "__main__":
    organize_files()
