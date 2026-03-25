import src.pg_mcp.database as db
import asyncio

async def main():
    pool = await db.get_pool()
    print("Created Connection Pool")

    result = await db.fetch_all(pool, "SELECT * FROM products")
    print(result)

    print("\nNow fetching single row: \n")
    result = await db.fetch_one(pool, "SELECT * FROM products WHERE id = 1")
    print(result)

    print("\nNow fetching all table names: \n")
    result = await db.get_table_names(pool)
    print(result)

    tables = result

    print("\nNow fetching table schemas: \n")
    for table in tables:
        result = await db.get_table_schema(pool, table)
        print(result, "\n")

    print("\nNow fetching row counts: \n")
    for table in tables:
        result = await db.get_row_count(pool, table)
        print("Rows in " + table + ":")
        print(result)
    
    await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
