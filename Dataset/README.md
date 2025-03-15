# Dataset Structure

This repository contains three datasets: Benchmark dataset, Knowledge Base dataset, and the complete Inter-app Dataset. Each dataset follows the same directory structure, with anonymized application names and records. Below is a detailed description of the dataset structure.

## Directory Structure

The datasets are organized as follows:

```
Dataset (Benchmark/Knowledge_Base/Inter-app Dataset)
|-- 1
|   |-- record_1.zip
|   |   |-- record.json
|   |   |-- screenshots
|   |   |   |-- step_0.png
|   |   |   |-- step_1.png
|   |   |   `-- ...
|   |   `-- ui_trees
|   |       |-- step_0_ui.xml
|   |       |-- step_1_ui.xml
|   |       `-- ...
|   |-- record_2.zip
|   |   |-- (same structure as above)
|   |   `-- ...
|   `-- 1.apk
|-- 2
|   |-- record_1.zip
|   |   |-- (same structure as above)
|   |   `-- ...
|   `-- 2.apk
|-- ...
```

### Structure Explanation

1. **Root Directory**: Each dataset contains multiple numbered directories (1, 2, 3, etc.), each representing a unique application. Note: Due to Google Play Store's copyright requirements, all application names have been anonymized and replaced with sequential numbers.

2. **Application Directory**: Each numbered directory contains:
   - Multiple `record_N.zip` files (where N starts from 1)
   - An application package file named `N.apk` or `N.xapk` (where N matches the directory name)

3. **Record ZIP Files**: Each `record_N.zip` contains:
   - `record.json`: Metadata and logs of the recording session
   - `screenshots` directory: Contains step-by-step screenshots
   - `ui_trees` directory: Contains XML files representing UI hierarchy for each step

4. **Screenshots Directory**: Contains PNG files named `step_N.png` (where N starts from 0)

5. **UI Trees Directory**: Contains XML files named `step_N_ui.xml` (where N matches the corresponding screenshot number)

### Dataset Categories

1. **Benchmark Dataset**: Contains test cases for evaluation
2. **Knowledge Base Dataset**: Contains training data (excludes test cases)
3. **Inter-app Dataset**: Complete dataset containing all records

### File Naming Convention

- Application directories: Numbered sequentially (1, 2, 3, ...) to maintain anonymity and comply with Google Play Store's terms of service
- Record files: Named `record_N.zip` where N starts from 1 within each application directory
- APK files: Named `N.apk` or `N.xapk` where N matches the parent directory number
- Screenshots: Named `step_N.png` where N starts from 0
- UI trees: Named `step_N_ui.xml` where N matches the corresponding screenshot number

### Recorded User Interactions

We write a tool to record user interactions on Android devices, and the code is available in [dataset_collection_tool](../Code/dataset_collection_tool/README.md).
Each record captures various types of user interactions:

- Click/Press: Marked with a blue dot for click position and red border for the operated element
- Swipe: Shown with blue dots for start/end points and an arrowed line indicating direction
- Text Input: Input content is displayed at the top of the screen
- Special Events: Event type is shown at the top of the screen

Note: All directory and file names have been anonymized for privacy, consistency, and compliance with Google Play Store's copyright requirements. The original application names and timestamps have been replaced with sequential numbers.

## Example Data

An example record from our dataset can be found in the [data_example](./data_example) directory, which demonstrates the structure and format of our collected data.

## Complete Dataset Access

The complete dataset is available on [Google Drive](https://drive.google.com/drive/folders/1P3jdUHk7iM9JWvow4gmwUYRcEoyqUw4j?usp=sharing)

Due to the storage limitations of Google Drive, [this link](https://drive.google.com/drive/folders/1P3jdUHk7iM9JWvow4gmwUYRcEoyqUw4j?usp=sharing) currently only provides the Inter-app Dataset containing APKs, as well as the Benchmark Dataset and Knowledge Base Dataset without the corresponding APKs. We will soon provide a complete cloud storage link that includes all the APKs.