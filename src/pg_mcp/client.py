import asyncio
import ollama
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

async def main():
    server_params = StdioServerParameters(
        command = "python",
        args = ["src/pg_mcp/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_response = await session.list_tools()

            available_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                for tool in tools_response.tools
            ]

            system_message = {
                "role": "system",
                "content": """You are a database assistant with access to a PostgreSQL database.
                To answer questions, you MUST use the available tools. Follow this exact process:
                1. Call list_tables to see available tables
                2. Call describe_table for each relevant table to get exact column names
                3. Call run_query with a SELECT statement to get the actual data
                4. Only after receiving real data from run_query, give your final answer
                Never describe a query without actually running it. Never guess or assume data."""
            }

            messages = [
                system_message,
            ]
            
            while True:
                question = input("You: ")
                if question.lower() in ["quit", "exit"]:
                    break
                
                messages.append({"role": "user", "content": question})

                while True:
                    chat_response = await ollama.AsyncClient().chat(
                        model=os.getenv("OLLAMA_MODEL"),
                        messages=messages,
                        tools=available_tools
                    )

                    if not chat_response.message.tool_calls:
                        print(chat_response.message.content)
                        break

                    messages.append({"role": "assistant", "content": "", "tool_calls": chat_response.message.tool_calls})
        
                    for tool_call in chat_response.message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments
                        tool_result = await session.call_tool(tool_name, tool_args)
                        messages.append({"role": "tool", "content": str(tool_result.content)})

if __name__ == "__main__":
    asyncio.run(main())