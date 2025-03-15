# InterDroid Code README

## Environment Setup

### 1. Android Studio Setup
1. Download Android Studio from [official website](https://developer.android.com/studio)
2. Install Android Studio following the installation wizard
3. Launch Android Studio and complete the initial setup

### 2. Android Virtual Device (AVD) Setup
1. Open Android Studio
2. Click "Tools" > "Device Manager" > "Create Virtual Device"
3. Select a device definition (e.g., Pixel 2)
4. Select a system image:
   - Choose x86 Images for better performance
   - Recommended: API 30 (Android 11.0) or higher
   - Download the system image if not available
5. Configure AVD settings:
   - Set device name
   - Adjust RAM size (recommended: 2GB or more)
   - Set internal storage (recommended: 2GB or more)
6. Click "Finish" to create the AVD

### 3. Physical Device Setup (Alternative)
1. Enable Developer Options on your Android device:
   - Go to Settings > About Phone
   - Tap "Build Number" 7 times
2. Enable USB debugging in Developer Options
3. Connect device via USB
4. Allow USB debugging on device when prompted

## Dataset Preparation

1. Download the dataset, Please refer to [dataset](../Dataset/README.md) for more details.
2. Install required dependencies:
```bash
conda create -n interdroid python=3.10
conda activate interdroid
pip install -r requirements.txt
```

## Data Processing Pipeline

### 1. Initial Data Processing
```bash
python preprocess_data_dir.py
```
This step filters and organizes the data, keeping only the record_xxxx directories.

### 2. Data Augmentation
```bash
python data_aug2.py
```
This generates augmented data in the `processed_screenshots` directory.

### 3. Generate App Descriptions
```bash
python generate_app_description.py
```
This step uses GPT to generate detailed app descriptions and stores them in the `gpt_app_description` field.

### 4. Embedding Generation
Process the dataset using an embedding model to generate vector representations.

You can use the API or build the dataset locally.

```bash
python build_rag_dataset_api.py
```

or

```bash
python build_rag_dataset_local.py
```

If you want to build the dataset locally, you need to download the model, see [GME](https://huggingface.co/Alibaba-NLP/gme-Qwen2-VL-2B-Instruct) for more details.


## Configuration

1. Modify the settings in `config.py` according to your needs:
   - API keys
   - Data paths
   - Android Device ID/Name

## Running the Code

```bash
python main.py
```

## Notes
- Ensure sufficient storage space for the dataset and processed data
- GPU is recommended for faster processing
- Check CUDA compatibility if using GPU

