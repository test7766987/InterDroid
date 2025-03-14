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

## Access

You can access the benchmark dataset through the following link:

[Google Drive](https://drive.google.com/drive/folders/1P3jdUHk7iM9JWvow4gmwUYRcEoyqUw4j?usp=sharing)




