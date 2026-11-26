import asyncio
import base64
import io
from pathlib import Path

from PIL import Image

from app.db.mongodb import database


async def main():
    upload_dir = Path(__file__).resolve().parents[1] / "uploads" / "disease"
    cursor = database.disease_predictions.find(
        {"status": "completed"},
    )
    records = await cursor.to_list(length=1000)
    updated = 0

    for record in records:
        if record.get("thumbnail_base64"):
            continue

        image_hash = record.get("image_hash")
        if not image_hash:
            continue

        candidates = sorted(upload_dir.glob(f"{image_hash}.*"))
        if not candidates:
            continue

        image_path = candidates[0]
        try:
            with Image.open(image_path) as source:
                thumbnail = source.convert("RGB")
                thumbnail.thumbnail((480, 480), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                thumbnail.save(buffer, format="JPEG", quality=82)
                thumbnail_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        except Exception:
            continue

        await database.disease_predictions.update_one(
            {"_id": record["_id"]},
            {
                "$set": {
                    "image_path": str(image_path).replace("\\", "/"),
                    "thumbnail_base64": thumbnail_base64,
                }
            },
        )
        updated += 1

    disease_count = await database.disease_predictions.count_documents({})
    print(f"disease_count={disease_count}")
    print(f"backfilled={updated}")


if __name__ == "__main__":
    asyncio.run(main())
