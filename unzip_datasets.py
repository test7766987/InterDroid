import os
import zipfile
import shutil

def unzip_record(zip_path, extract_dir):
    """Extract a single record zip file"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        return True
    except Exception as e:
        print(f"Error extracting file {zip_path}: {e}")
        return False

def process_app_directory(app_dir):
    """Process all record zip files in a single APP directory"""
    print(f"Processing directory: {app_dir}")
    
    # Get all record zip files
    record_files = [f for f in os.listdir(app_dir) 
                   if f.startswith('record_') and f.endswith('.zip')]
    
    for zip_file in record_files:
        zip_path = os.path.join(app_dir, zip_file)
        # Create extraction target directory (remove .zip extension)
        extract_dir = os.path.join(app_dir, zip_file[:-4])
        
        try:
            # If target directory already exists, delete it first
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            
            # Extract file
            if unzip_record(zip_path, extract_dir):
                print(f"Extracted: {zip_file}")
                # Delete zip file
                os.remove(zip_path)
                print(f"Deleted: {zip_file}")
            else:
                print(f"Extraction failed: {zip_file}")
                
        except Exception as e:
            print(f"Error processing file {zip_file}: {e}")
            continue

def unzip_dataset(dataset_dir):
    """Process the entire dataset directory"""
    if not os.path.exists(dataset_dir):
        print(f"Directory does not exist: {dataset_dir}")
        return
    
    print(f"\nStarting to process dataset: {dataset_dir}")
    
    # Get all numerically named directories
    app_dirs = [d for d in os.listdir(dataset_dir) 
               if os.path.isdir(os.path.join(dataset_dir, d)) and d.isdigit()]
    
    # Process each application directory in numerical order
    for app_dir in sorted(app_dirs, key=int):
        app_path = os.path.join(dataset_dir, app_dir)
        process_app_directory(app_path)

def main():
    # Set dataset directories
    dataset_dirs = [
        "Benchmark",
        "Inter-app Dataset",
        "Knowledge_Base_without_apk"
    ]
    
    try:
        for dataset_dir in dataset_dirs:
            unzip_dataset(dataset_dir)
        print("\nAll record files processed successfully!")
    except Exception as e:
        print(f"\nError during processing: {e}")

if __name__ == "__main__":
    main()