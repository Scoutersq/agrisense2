import asyncio
from app.db.mongodb import database


async def main():
    record = await database.disease_predictions.find_one({"status": "completed"})
    print({
        "image_name": record.get("image_name"),
        "disease": record.get("predicted_class"),
        "thumbnail_chars": len(record.get("thumbnail_base64", "")),
        "image_path": record.get("image_path"),
    })


if __name__ == "__main__":
    asyncio.run(main())
