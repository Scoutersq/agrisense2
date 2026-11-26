import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2
from tqdm import tqdm


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def evaluate(model, loader, device):
    model.eval()
    targets = []
    predictions = []
    with torch.inference_mode():
        for images, labels in tqdm(loader, desc="Test evaluation", leave=False):
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            predicted = outputs.argmax(dim=1)
            targets.extend(labels.cpu().numpy().tolist())
            predictions.extend(predicted.cpu().numpy().tolist())
    return np.asarray(targets), np.asarray(predictions)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=r"D:\agrisense\ml\datasets\processed\PlantVillage")
    parser.add_argument("--output", default=r"D:\agrisense\ml\saved_models")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=0.0005)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    seed_everything(args.seed)
    data_root = Path(args.data)
    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)

    train_dir = data_root / "train"
    validation_dir = data_root / "validation"
    test_dir = data_root / "test"
    for directory in (train_dir, validation_dir, test_dir):
        if not directory.exists():
            raise FileNotFoundError(f"Missing split directory: {directory}")

    normalization = MobileNet_V2_Weights.DEFAULT.transforms()
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.80, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(12),
        transforms.ColorJitter(brightness=0.12, contrast=0.12, saturation=0.12),
        normalization,
    ])
    evaluation_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        normalization,
    ])

    train_data = datasets.ImageFolder(train_dir, transform=train_transform)
    validation_data = datasets.ImageFolder(validation_dir, transform=evaluation_transform)
    test_data = datasets.ImageFolder(test_dir, transform=evaluation_transform)
    if train_data.classes != validation_data.classes or train_data.classes != test_data.classes:
        raise RuntimeError("Train, validation, and test class lists do not match")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pin_memory = device.type == "cuda"
    train_loader = DataLoader(
        train_data,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=pin_memory,
    )
    validation_loader = DataLoader(
        validation_data,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory,
    )
    test_loader = DataLoader(
        test_data,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory,
    )

    model = mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(train_data.classes))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.0001)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    best_validation_loss = float("inf")
    history = []

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        progress = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{args.epochs}")
        for images, labels in progress:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += labels.size(0)
            progress.set_postfix(loss=loss.item())

        model.eval()
        validation_loss = 0.0
        with torch.inference_mode():
            for images, labels in validation_loader:
                images = images.to(device)
                labels = labels.to(device)
                validation_loss += criterion(model(images), labels).item() * images.size(0)
        validation_loss /= len(validation_data)
        training_accuracy = correct / total
        epoch_record = {
            "epoch": epoch + 1,
            "training_accuracy": training_accuracy,
            "validation_loss": validation_loss,
            "device": str(device),
        }
        history.append(epoch_record)
        print(json.dumps(epoch_record))

        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            torch.save({
                "model_state_dict": model.state_dict(),
                "class_names": train_data.classes,
                "image_size": 224,
                "normalization": "MobileNet_V2_Weights.DEFAULT",
            }, output_root / "crop_disease_mobilenetv2.pt")
        scheduler.step()

    checkpoint = torch.load(output_root / "crop_disease_mobilenetv2.pt", map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    targets, predictions = evaluate(model, test_loader, device)
    cm = confusion_matrix(targets, predictions, labels=list(range(len(train_data.classes))))
    metrics = {
        "dataset": "PlantVillage",
        "license": "verify source license and redistribution terms before publication",
        "architecture": "MobileNetV2 transfer learning",
        "device": str(device),
        "seed": args.seed,
        "image_size": 224,
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "split_sizes": {
            "train": len(train_data),
            "validation": len(validation_data),
            "test": len(test_data),
        },
        "class_names": train_data.classes,
        "test_accuracy": float(accuracy_score(targets, predictions)),
        "test_precision_macro": float(precision_score(targets, predictions, average="macro", zero_division=0)),
        "test_recall_macro": float(recall_score(targets, predictions, average="macro", zero_division=0)),
        "test_f1_macro": float(f1_score(targets, predictions, average="macro", zero_division=0)),
        "confusion_matrix": cm.tolist(),
        "history": history,
    }
    (output_root / "crop_disease_classes.json").write_text(
        json.dumps(train_data.classes, indent=2),
        encoding="utf-8",
    )
    (output_root / "crop_disease_metrics.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
