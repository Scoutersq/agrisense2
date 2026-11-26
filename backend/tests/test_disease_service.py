from pathlib import Path

import pytest
import torch
from PIL import Image

from app.services.disease_service import DiseaseInferenceService


MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "saved_models" / "crop_disease_mobilenetv2.pt"
CLASSES_PATH = Path(__file__).resolve().parents[2] / "ml" / "saved_models" / "crop_disease_classes.json"


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Disease model not present")
def test_disease_service_inference_shape():
    service = DiseaseInferenceService(MODEL_PATH, CLASSES_PATH)
    image = Image.new("RGB", (224, 224), color=(55, 115, 62))
    predictions = service.predict(image, top_k=3)

    assert len(predictions) == 3
    assert all("class_name" in item for item in predictions)
    assert all(0.0 <= item["probability"] <= 1.0 for item in predictions)
