# Knowledge Base Dataset

This knowledge base contains structured information about inter-app functionalities extracted from real-world mobile applications. It is designed to support the InterDroid automated GUI testing approach by providing a comprehensive repository of historical inter-app interactions. The knowledge base integrates both visual and textual GUI information to enhance retrieval accuracy and facilitate effective memory implantation in Large Language Models (LLMs).

## Data Collection
The knowledge base is constructed from a subset of the Android in the Wild dataset, which includes human demonstrations of device interactions. We randomly selected 500 apps and analyzed their AndroidManifest.xml files to identify inter-app functionalities. A total of 763 inter-app functionalities were collected, and 150 functionalities from 89 apps were selected for the knowledge base.

## Categories of Inter-app Functionalities
The inter-app functionalities in the knowledge base are categorized into five types:
1. ​**Sharing (29%)**: Involves sharing content between apps, such as files, images, posts, or links.
2. ​**System/OS Setting (22%)**: Manages system-level permissions or settings through inter-app actions.
3. ​**Third-party Service (21%)**: Includes interactions with external content, such as reviews, feedback, and payments.
4. ​**Info Synchronization (15%)**: Involves the synchronization of user data across different applications or services.
5. ​**Authentication (13%)**: Encompasses authentication processes that require users to verify their identity through external platforms.

## Dataset Structure

The knowledge base dataset follows the standard structure as described in the main dataset documentation:

```
Knowledge_Base
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

You can access the knowledge base dataset through the following link:

[Google Drive](https://drive.google.com/drive/folders/1P3jdUHk7iM9JWvow4gmwUYRcEoyqUw4j?usp=sharing)

Please note that due to the storage limitations of Google Drive, only the complete Inter-app Dataset (with corresponding APKs for each app) and the complete Knowledge Base Dataset (which does not require APKs) are available in [the above Google Drive link](https://drive.google.com/drive/folders/1P3jdUHk7iM9JWvow4gmwUYRcEoyqUw4j?usp=sharing). Due to storage constraints, the Benchmark Dataset is provided without the associated APKs. However, we have made the complete Benchmark Dataset, including the corresponding APKs for each app, available in [a separate Google Drive link](https://drive.google.com/drive/folders/1rC_OTxIg5bqFRVaY636bfPOpV_P8-1eE?usp=sharing).
