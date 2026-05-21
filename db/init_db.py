import asyncio
from db.database import init_db

async def main():
    await init_db()
    print("DB tables created.")

asyncio.run(main())
