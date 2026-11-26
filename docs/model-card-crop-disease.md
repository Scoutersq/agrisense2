# PlantVillage Crop Disease Model Card

## Architecture

- MobileNetV2 transfer learning
- 224x224 input images
- MobileNetV2 default ImageNet normalization
- 15 PlantVillage classes

## Training

- Train/validation/test split: 14,440 / 3,089 / 3,109
- Seed: 42
- Batch size: 16
- Learning rate: 0.0005
- Optimizer: AdamW
- Weight decay: 0.0001
- Epochs: 10
- CPU device used for measured run

## Measured held-out test performance

- Accuracy: 99.3245%
- Macro precision: 99.1514%
- Macro recall: 99.3473%
- Macro F1: 99.2436%

The complete confusion matrix and training history are stored in
`ml/saved_models/crop_disease_metrics.json`.

## Limitations

The model was trained on PlantVillage-style controlled leaf photographs. It may
misclassify real field images, multiple-leaf scenes, blurred images, unfamiliar
crops, healthy stress, or previously unseen diseases. Predictions are
AI-assisted screening results, not confirmed diagnoses. Laboratory testing or
qualified local agricultural advice is required before high-impact decisions.
