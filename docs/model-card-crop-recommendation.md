# Crop Recommendation Model Card

## Dataset

Kaggle Crop Recommendation Dataset, CC BY 3.0 IGO.

Source: https://www.kaggle.com/datasets/siddharthss/crop-recommendation-dataset

## Features

- Nitrogen
- Phosphorus
- Potassium
- Temperature
- Humidity
- Soil pH
- Rainfall

## Training

- 2,200 rows after duplicate and missing-value removal
- 80% training and 20% held-out test split
- Stratified split with random state 42
- Five-fold stratified cross-validation
- Algorithms compared: Decision Tree, K-Nearest Neighbors, Random Forest, XGBoost
- Selected model: Random Forest

## Actual measured results

- Held-out test accuracy: 99.3182%
- Five-fold cross-validation mean accuracy: 99.375%
- XGBoost held-out test accuracy: 99.0909%
- Decision Tree held-out test accuracy: 97.9545%
- KNN held-out test accuracy: 97.0455%

Full metrics are saved in `ml/saved_models/crop_recommendation_metrics.json`.

## Limitations

The dataset is not a complete representation of Indian farms or real-world soil conditions. It does not guarantee crop suitability or yield. Local soil testing and agricultural expert advice remain necessary.
