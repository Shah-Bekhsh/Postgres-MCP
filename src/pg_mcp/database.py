import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def get_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        host = os.getenv("DB_HOST"),
        port = int(os.getenv("DB_PORT")),
        database = os.getenv("DB_NAME"),
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        min_size= 1,
        max_size=5
    )

async def fetch_all(pool: asyncpg.Pool, query:str, *args):
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, *args)
        return [dict(row) for row in rows]
    
async def fetch_one(pool: asyncpg.Pool, query:str, *args):
    async with pool.acquire() as connection:
        row = await connection.fetchrow(query, *args)
        return dict(row) if row else None

async def get_table_names(pool: asyncpg.Pool):
    prepared_statement = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    results = await fetch_all(pool=pool, query=prepared_statement)
    return [result["table_name"] for result in results]

async def get_table_schema(pool: asyncpg.Pool, table_name: str):
    prepared_statement = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = $1
        ORDER BY ordinal_position
    """
    result = await fetch_all(pool, prepared_statement, table_name)
    return result

async def get_row_count(pool: asyncpg.Pool, table_name: str):
    prepared_statement = f"SELECT COUNT(*) AS count FROM {table_name}"

    result = await fetch_one(pool, prepared_statement)

    return result["count"]
