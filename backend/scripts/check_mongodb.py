import asyncio

from app.core.config import settings
from app.db.mongodb import client, database


async def main() -> None:
    ping = await client.admin.command("ping")
    user_count = await database.users.count_documents({})
    probe = await database.users.insert_one({"_probe": True, "purpose": "mongodb-write-test"})
    probe_written = await database.users.count_documents({"_id": probe.inserted_id}) == 1
    await database.users.delete_one({"_id": probe.inserted_id})
    print(f"mongodb_connection={ping.get('ok') == 1}")
    print(f"database={settings.mongodb_db}")
    print(f"user_count={user_count}")
    print(f"write_probe={probe_written}")


if __name__ == "__main__":
    asyncio.run(main())
