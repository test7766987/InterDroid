import os
import shutil
import json
from pathlib import Path

def process_directory(base_path):
    # Traverse the base directory
    for category_dir in os.listdir(base_path):
        category_path = os.path.join(base_path, category_dir)
        if not os.path.isdir(category_path):
            continue
            
        print(f"Processing directory: {category_dir}")
        
        # Traverse application directories under each category directory
        for app_dir in os.listdir(category_path):
            app_path = os.path.join(category_path, app_dir)
            if not os.path.isdir(app_path):
                continue
                
            # Traverse record directories under each application directory
            for record_dir in os.listdir(app_path):
                record_path = os.path.join(app_path, record_dir)
                if not os.path.isdir(record_path) or not record_dir.startswith('record_'):
                    continue
                    
                # Move screenshots and ui_trees directories
                for dir_name in ['screenshots', 'ui_trees']:
                    src_dir = os.path.join(record_path, dir_name)
                    if os.path.exists(src_dir):
                        dst_dir = os.path.join(app_path, dir_name)
                        # If target directory exists, delete it first
                        if os.path.exists(dst_dir):
                            shutil.rmtree(dst_dir)
                        shutil.move(src_dir, dst_dir)
                
                # Move and process record.json file
                json_file = os.path.join(record_path, 'record.json')
                if os.path.exists(json_file):
                    dst_file = os.path.join(app_path, 'record.json')
                    # Read JSON file
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Delete gpt_app_description field
                    if 'gpt_app_description' in data:
                        del data['gpt_app_description']

                    if 'app_combined_description' in data:
                        del data['app_combined_description']
                    
                    # Write new JSON file to target location
                    with open(dst_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    
                    # Delete original file
                    os.remove(json_file)
                
                # Delete record_xxx directory
                shutil.rmtree(record_path)

if __name__ == "__main__":
    # Set base path to test dataset directory
    base_path = r"C:\Users\Username\Desktop\test_dataset"
    
    try:
        process_directory(base_path)
        print("All directories processed successfully!")
    except Exception as e:
        print(f"Error occurred during processing: {str(e)}")
