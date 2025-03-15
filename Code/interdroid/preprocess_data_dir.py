import os
import shutil
import re

def process_directories(source_dir='data', target_dir='real_data'):
    """
    Recursively process the source directory, find all directories matching the record_xxxx pattern
    and copy them to the target directory
    
    Args:
        source_dir: Source directory path
        target_dir: Target directory path
    """
    # Ensure target directory exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # Compile regex pattern
    pattern = re.compile(r'^record_\d{8}_\d{6}$')  # Match record_YYYYMMDD_HHMMSS format
    
    # Traverse source directory
    for root, dirs, files in os.walk(source_dir):
        for dir_name in dirs:
            # Check if directory name matches record_xxxx pattern
            if pattern.match(dir_name):
                source_path = os.path.join(root, dir_name)
                target_path = os.path.join(target_dir, dir_name)
                
                # If target path exists, add suffix to avoid overwriting
                if os.path.exists(target_path):
                    base_path = target_path
                    counter = 1
                    while os.path.exists(target_path):
                        target_path = f"{base_path}_{counter}"
                        counter += 1
                
                print(f"Copying directory: {source_path} -> {target_path}")
                try:
                    shutil.copytree(source_path, target_path)
                except Exception as e:
                    print(f"Error occurred while copying directory {source_path}: {str(e)}")

if __name__ == "__main__":
    # Process directories
    process_directories(r'C:\Users\Username\Desktop\test_dataset')
    print("Processing complete!") 