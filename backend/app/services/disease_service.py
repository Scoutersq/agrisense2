import json
from pathlib import Path

import torch
from torch import nn
from torchvision import transforms
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2
from PIL import Image


class DiseaseInferenceService:
    def __init__(self, model_path: Path, classes_path: Path):
        if not model_path.exists():
            raise FileNotFoundError(f"Disease model not found: {model_path}")
        if not classes_path.exists():
            raise FileNotFoundError(f"Disease classes not found: {classes_path}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.class_names = json.loads(classes_path.read_text(encoding="utf-8"))
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)

        checkpoint_classes = checkpoint.get("class_names")
        if checkpoint_classes:
            if checkpoint_classes != self.class_names:
                raise RuntimeError("Checkpoint class names do not match the classes JSON")

        self.model = mobilenet_v2(weights=None)
        self.model.classifier[1] = nn.Linear(
            self.model.classifier[1].in_features,
            len(self.class_names),
        )
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        normalization = MobileNet_V2_Weights.DEFAULT.transforms()
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            normalization,
        ])

    def predict(self, image: Image.Image, top_k: int = 3):
        with torch.inference_mode():
            tensor = self.transform(image.convert("RGB")).unsqueeze(0).to(self.device)
            probabilities = torch.softmax(self.model(tensor), dim=1)[0]

        values, indices = torch.topk(
            probabilities,
            k=min(top_k, len(self.class_names)),
        )
        top_predictions = [
            {
                "class_name": self.class_names[int(index)],
                "probability": round(float(value), 4),
                "confidence_percent": round(float(value) * 100, 2),
            }
            for value, index in zip(values.cpu(), indices.cpu())
        ]
        return top_predictions
