# AgriSense ML Datasets

## Crop Recommendation

- File: `raw/Crop_recommendation.csv`
- Source: Kaggle Crop Recommendation Dataset
- Kaggle page: https://www.kaggle.com/datasets/siddharthss/crop-recommendation-dataset
- License: Attribution 3.0 IGO (CC BY 3.0 IGO)
- Features: N, P, K, temperature, humidity, pH, rainfall
- Target: suitable crop label
- Preprocessing: duplicate removal, missing-value removal, stratified train/test split

The dataset is suitable for a project/modeling baseline, not a guarantee of suitability for every Indian farm.

## PlantVillage Disease Dataset

- Archive: `raw/PlantVillage.zip`
- Dataset page: `emmarex/plantdisease` on Kaggle
- License and redistribution terms must be verified on Kaggle before publication
- Images: JPG/PNG
- Task: 38-class or class-subset crop disease classification
- Required preprocessing: corruption check, MIME validation, resize to model input, normalization
