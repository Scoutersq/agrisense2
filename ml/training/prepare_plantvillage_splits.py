import argparse
import json
import random
import shutil
from pathlib import Path

from PIL import Image


def find_class_roots(root: Path) -> list[Path]:
    candidates = []
    for candidate in root.rglob("*"):
        if not candidate.is_dir():
            continue
        class_dirs = [
            child for child in candidate.iterdir()
            if child.is_dir()
            and any(child.glob("*"))
        ]
        image_count = sum(
            1 for child in candidate.rglob("*")
            if child.is_file() and child.suffix.lower() in {".jpg", ".jpeg", ".png"}
        )
        if len(class_dirs) >= 10 and image_count >= 1000:
            candidates.append(candidate)
    return sorted(set(candidates), key=lambda path: len(str(path)))


def prepare(source: Path, destination: Path, seed: int = 42) -> dict:
    random.seed(seed)
    destination = destination.resolve()
    if destination.exists():
        shutil.rmtree(destination)

    class_dirs = [
        path for path in source.iterdir()
        if path.is_dir()
        and any(
            child.is_file() and child.suffix.lower() in {".jpg", ".jpeg", ".png"}
            for child in path.iterdir()
        )
    ]
    if len(class_dirs) < 10:
        raise ValueError(f"Expected class directories under {source}, found {len(class_dirs)}")

    corrupted = []
    class_counts = {}
    for class_dir in sorted(class_dirs):
        images = [
            path for path in class_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ]
        valid = []
        for image_path in images:
            try:
                with Image.open(image_path) as image:
                    image.verify()
                valid.append(image_path)
            except Exception:
                corrupted.append(str(image_path))
        class_counts[class_dir.name] = len(valid)

        random.shuffle(valid)
        train_end = int(len(valid) * 0.70)
        validation_end = train_end + int(len(valid) * 0.15)
        for split, split_images in (
            ("train", valid[:train_end]),
            ("validation", valid[train_end:validation_end]),
            ("test", valid[validation_end:]),
        ):
            for image_path in split_images:
                target = destination / split / class_dir.name / image_path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(image_path, target)

    result = {
        "source": str(source),
        "destination": str(destination),
        "seed": seed,
        "classes": len(class_counts),
        "class_counts": class_counts,
        "corrupted_images": len(corrupted),
        "split_ratio": {"train": 0.70, "validation": 0.15, "test": 0.15},
    }
    metrics_path = destination.parent / "plantvillage_split_audit.json"
    metrics_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        nargs="?",
        default=r"D:\agrisense\ml\datasets\raw\PlantVillage_extracted\PlantVillage",
    )
    parser.add_argument(
        "destination",
        nargs="?",
        default=r"D:\agrisense\ml\datasets\processed\PlantVillage",
    )
    args = parser.parse_args()
    prepare(Path(args.source), Path(args.destination))


if __name__ == "__main__":
    main()
