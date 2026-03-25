from mcp.server.fastmcp import FastMCP
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.pg_mcp.database as db
from contextlib import asynccontextmanager
from dotenv import load_dotenv


load_dotenv()

pool = None

@asynccontextmanager
async def lifespan(app):
    global pool
    pool = await db.get_pool()
    yield 
    await pool.close()

mcp = FastMCP("pg-mcp", lifespan=lifespan)

@mcp.tool()
async def list_tables():
    """Returns a list of all the tables in the database"""
    result = await db.get_table_names(pool)
    return result

@mcp.tool()
async def describe_table(table_name: str):
    """Takes a table name as argument and returns the information schema for that table"""
    result = await db.get_table_schema(pool, table_name)
    return result

@mcp.tool()
async def run_query(query: str):
    """Takes a prepared SQL Query, executes it and returns the result. ONLY SELECT Queries are accepted. If the SQL Query is anything except SELECT, return an error message saying \"Only SELECT Queries allowed\""""
    result = None
    if query.lower().startswith("select"):
        result = await db.fetch_all(pool, query)
    else:
        result = f"Error. Only SELECT queries allowed."
    return result

@mcp.resource("schema://database")
async def get_database_schema():
    """Returns the full database schema - all tables and their columns - as a single readable document."""
    db_schema = ""
    tables = await db.get_table_names(pool)
    
    for table_name in tables:
        schema = await db.get_table_schema(pool, table_name)
        db_schema += f"\nTable: {table_name}\n"
        for table in schema:
            db_schema += f"  Column: {table['column_name']}, Type: {table['data_type']}\n"
    return db_schema

if __name__ == "__main__":
    mcp.run()