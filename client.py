"""
Model Context Protocol (MCP) Chatbot Client

This module implements a chatbot client that connects to MCP servers and interacts with
the Anthropic Claude API. It provides a command-line interface for users to query
the system, which can then utilize various tools provided by connected MCP servers.

The client supports:
- Multiple MCP server connections
- Tool discovery and management
- Interactive chat interface
- Anthropic Claude API integration
- Asynchronous operation

Requirements:
    - Python 3.7+
    - Anthropic API key in .env file
    - server_config.json with MCP server configurations
"""

from contextlib import AsyncExitStack
import json
from typing import Dict, List, TypedDict
from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import nest_asyncio
import os
import asyncio

nest_asyncio.apply()

load_dotenv()


class ToolDefinition(TypedDict):
    """Type definition for MCP tool configuration.
    
    Attributes:
        name: The name of the tool
        description: A description of what the tool does
        input_schema: JSON schema defining the tool's input parameters
    """
    name: str
    description: str
    input_schema: dict


class MCP_ChatBot:
    """A chatbot that integrates with MCP servers and the Anthropic Claude API.
    
    This class manages connections to MCP servers, discovers available tools,
    and processes user queries using the Anthropic Claude API while coordinating
    tool calls across different MCP server sessions.
    
    Attributes:
        sessions: List of active MCP server sessions
        exit_stack: AsyncExitStack for managing async context managers
        anthropic: Anthropic API client instance
        available_tools: List of all available tools across all connected servers
        tool_to_session: Mapping of tool names to their respective server sessions
    """

    def __init__(self):
        """Initialize the chatbot with empty sessions and tool registries."""
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic(api_key=os.getenv("API_KEY"))
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server and register its tools.
        
        Args:
            server_name: Name identifier for the server
            server_config: Configuration dictionary for the server connection
        
        Raises:
            Exception: If connection fails or tool registration encounters an error
        """
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)

            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools: {[t.name for t in tools]}")

            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                )
        except Exception as e:
            print(f"Failed to connect to {server_name}:  {e}")

    async def connect_to_servers(self) -> None:
        """Connect to all MCP Servers defined in server_config.json.
        
        The configuration file should define a dictionary of server configurations
        under the 'mcpServers' key.
        
        Raises:
            Exception: If the config file cannot be read or if connection fails
        """
        try:
            with open("server_config.json") as file:
                data = json.load(file)

            servers = data.get("mcpServers", {})

            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server config: {e}")
            raise e

    async def process_query(self, query: str) -> None:
        """Process a user query using Claude and handle any tool calls.
        
        This method sends the query to Claude, interprets the response,
        executes any requested tool calls, and manages the conversation flow
        until a final response is reached.
        
        Args:
            query: The user's input query string
        """
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
                    messages.append({"role": "assistant", "content": assistant_content})
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name

                    print(f"Calling tool {tool_name} with {tool_args}")
                    session = self.tool_to_session[tool_name]
                    result = await session.call_tool(tool_name, tool_args)
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

    async def chat_loop(self) -> None:
        """Run the main interactive chat loop.
        
        Continuously prompts for user input and processes queries until
        the user types 'quit'. Handles errors gracefully and displays
        them to the user.
        """
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

    async def cleanup(self) -> None:
        """Clean up resources by closing all MCP server connections.
        
        Should be called when shutting down the chatbot to ensure proper
        cleanup of resources and connections.
        """
        await self.exit_stack.aclose()


async def main() -> None:
    """Entry point for the MCP chatbot application.
    
    Creates a chatbot instance, connects to configured servers,
    runs the chat loop, and ensures proper cleanup on exit.
    """
    chatbot = MCP_ChatBot()

    try:
        # Create MCP client sessions 
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
