# Knowledge Base Dataset

This directory contains the knowledge base dataset used for training automated app testing approaches. The knowledge base consists of carefully collected interaction records that capture various user behaviors and app functionalities.

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

## Knowledge Collection Criteria

The knowledge base records were collected based on the following criteria:

1. **Interaction Coverage**: Records that demonstrate:
   - Common user interaction patterns
   - Complex multi-step operations
   - Cross-application workflows
   - Error handling scenarios

2. **App Functionality Diversity**: Records covering:
   - Core app features
   - Different navigation paths
   - Various UI states
   - Inter-app communications

3. **Quality Assurance**: Each record is:
   - Manually verified
   - Properly annotated
   - Free of redundant steps
   - Representative of real user behavior

## Access

You can access the knowledge base dataset through the following link:

[Google Drive](https://drive.google.com/drive/folders/1P3jdUHk7iM9JWvow4gmwUYRcEoyqUw4j?usp=sharing)
