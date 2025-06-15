from typing import List
from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import nest_asyncio
import os
import asyncio

nest_asyncio.apply()

load_dotenv()


class MCP_ChatBot:
    def __init__(self):
        self.session: ClientSession = None
        self.anthropic = Anthropic(api_key=os.getenv("API_KEY"))
        self.available_tools: List[dict] = []

    async def process_query(self, query):
        messages = [{"role": "user", "content": query}]
        response = self.anthropic.messages.create(
            max_tokens=2024,
            model="claude-3-7-sonnet-20250219",
            tools=self.available_tools,
            messages=messages,
        )

        process_query = True
        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type == "text":
                    print(content.text)
                    assistant_content.append(content)
                    if len(response.content) == 1:
                        process_query = False
                elif content.type == "tool_use":
                    assistant_content.append(content)
                    messages.append(
                        {"role": "assistant", "content": assistant_content}
                    )
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name

                    print(f"Calling tool {tool_name} with {tool_args}")
                    result = await self.session.call_tool(tool_name, tool_args)
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": result.content,
                                }
                            ],
                        }
                    )
                    response = self.anthropic.messages.create(
                        max_tokens=2024,
                        model="claude-3-7-sonnet-20250219",
                        tools=self.available_tools,
                        messages=messages,
                    )
                    if (
                        len(response.content) == 1
                        and response.content[0].type == "text"
                    ):
                        print(response.content[0].text)
                        process_query = False

    async def chat_loop(self):
        print("\nMCP Chatbot Started")
        print("Enter queries or type 'quit' to exit")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break

                await self.process_query(query)
                print("\n")
            except Exception as e:
                print(f"\nError: {str(e)}")

    async def connect_to_server_and_run(self):
        server_params = StdioServerParameters(
            command="uv", args=["run", "server.py"], env=None
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # init connection to server
                await session.initialize()
                # Get list of available tools
                response = await session.list_tools()
                tools = response.tools

                self.available_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in tools
                ]

                await self.chat_loop()


async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()


if __name__ == "__main__":
    asyncio.run(main())
