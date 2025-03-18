# Benchmark Dataset

This benchmark is designed to evaluate the effectiveness of automated GUI testing tools, particularly for inter-app functionalities. It includes a carefully curated set of 100 inter-app functionalities from 63 real-world mobile applications. The benchmark is constructed to reflect the distribution of inter-app functionalities observed in the wild, ensuring that it provides a realistic testing environment.

## Data Collection
The benchmark is derived from the Android in the Wild dataset, which contains human demonstrations of device interactions. We manually selected 100 inter-app functionalities from 63 apps, ensuring that the functionalities cover all five categories identified in our pilot study:
1. ​**Sharing (29%)**
2. ​**System/OS Setting (22%)**
3. ​**Third-party Service (21%)**
4. ​**Info Synchronization (15%)**
5. ​**Authentication (13%)**

## Test Cases
Each inter-app functionality in the benchmark is accompanied by a set of test cases, including:
- ​**Test Scripts**: Manually written scripts that describe the steps to execute the functionality.
- ​**GUI Screenshots**: Screenshots of the GUI at each step of the interaction.
- ​**View Hierarchy Files**: Files that describe the structure of the GUI, including UI elements and their properties.

## Evaluation Metrics
The benchmark is evaluated using the following metrics:
- ​**Page Coverage**: The percentage of pages in the app that are covered by the test.
- ​**Action Coverage**: The percentage of actions that are executed during the test.
- ​**Exact Match Accuracy (EM)**: The percentage of instances where the predicted sequence of actions exactly matches the ground-truth sequence.

## Dataset Structure
The benchmark dataset follows the standard structure as described in the main dataset documentation:

```
Benchmark
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
|   |-- (same structure as above)
`-- ...
```

## Using Interdroid for Benchmark Evaluation

The following section describes Interdroid as an example implementation for benchmark evaluation. For new methods, you can implement the abstract interface defined in `testing_tool.py` or modify the code according to your specific requirements. The abstract interface provides a foundation that can be extended to create custom testing tools while maintaining compatibility with the benchmark evaluation framework.

Interdroid is a tool designed to evaluate automated testing approaches against this benchmark. It uses LLM-based intelligent testing to generate test actions and can calculate various coverage metrics.

### Prerequisites

1. Python 3.8 or higher
2. Android emulator or physical device
3. OpenAI API key
4. Required Python packages (install via `pip install -r requirements.txt`)

### Configuration

Before running Interdroid, you need to create a `config.ini` file with the following structure:

```ini
[llm]
openai_api_key = your_openai_api_key_here
openai_model = gpt-4-vision-preview

[uiautomator2]
android_device = emulator-5554

[data]
data_dir = /path/to/KnowledgeBase
```

Replace the values with your specific configuration:
- `openai_api_key`: Your OpenAI API key
- `openai_model`: The OpenAI model to use (default: gpt-4-vision-preview)
- `android_device`: The Android device ID (use `adb devices` to find it)
- `data_dir`: The path to the Benchmark directory

### Basic Usage

To run Interdroid with the default settings:

```bash
python -m benchmark_script.benchmark -o ./output
```

This will:
1. Start the LLM-based intelligent testing
2. Generate test actions based on the current UI
3. Save the results to the specified output directory

### Advanced Options

Interdroid supports several command-line options:

```bash
python -m benchmark_script.benchmark -o ./output [OPTIONS]
```

Available options:

- `--case INT`: Specify which test case to run from the Benchmark
- `--time DURATION`: Test duration, format: hours(6h), minutes(6m), or seconds(6s), default: 6h
- `--repeat INT`: Number of times to repeat the test, default: 1
- `--wait INT`: Idle time to wait before testing (seconds)
- `--record RECORD_ID`: Specific record to use as reference (e.g., "record_1")

### Evaluation Metrics

To calculate evaluation metrics, add the following flags:

- `--page-coverage`: Calculate page coverage
- `--action-coverage`: Calculate action coverage
- `--exact-match`: Calculate exact match rate

Example:

```bash
python -m benchmark_script.benchmark -o ./output --case 1 --page-coverage --action-coverage --exact-match
```

This will run the test on case 1 and calculate all three metrics.

### Interpreting Results

After running Interdroid, you'll find the following in your output directory:

- `args.json`: The command-line arguments used
- `screenshots/`: Directory containing screenshots of each step
- `actions.json`: The sequence of actions performed
- `results.json`: Evaluation metrics including page coverage, action coverage, and exact match rate

The `results.json` file will contain detailed information about:
- Percentage of pages covered
- Percentage of actions covered
- Exact match accuracy
- Details about covered and uncovered transitions

## Access

You can access the benchmark dataset through the following link:

[Google Drive](https://drive.google.com/drive/folders/1P3jdUHk7iM9JWvow4gmwUYRcEoyqUw4j?usp=sharing)

Please note that due to the storage limitations of Google Drive, only the complete Inter-app Dataset (with corresponding APKs for each app) and the complete Knowledge Base Dataset (which does not require APKs) are available in [the above Google Drive link](https://drive.google.com/drive/folders/1P3jdUHk7iM9JWvow4gmwUYRcEoyqUw4j?usp=sharing). Due to storage constraints, the Benchmark Dataset is provided without the associated APKs. However, we have made the complete Benchmark Dataset, including the corresponding APKs for each app, available in [a separate Google Drive link](https://drive.google.com/drive/folders/1rC_OTxIg5bqFRVaY636bfPOpV_P8-1eE?usp=sharing).




