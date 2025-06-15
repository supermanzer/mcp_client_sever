from dotenv import load_dotenv
import anthropic
import os
from server import tools, execute_tool

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("API_KEY"))


def process_query(query):
    messages = [{"role": "user", "content": query}]
    response = client.messages.create(
        max_tokens=2024,
        model="claude-3-7-sonnet-20250219",
        tools=tools,
        messages=messages,
    )
    process_query = True
    while process_query:
        assistant_content = []

        for content in response.content:
            if content.type == "text":
                print(content.text)
                assistant_content.append(content)

            elif content.type == "tool_use":
                assistant_content.append(content)
                messages.append({"role": "assistant", "content": assistant_content})

                tool_id = content.id
                tool_args = content.input
                tool_name = content.name
                print(f"calling {tool_name} with {tool_args}")

                result = execute_tool(tool_name=tool_name, tool_args=tool_args)
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": result,
                            }
                        ],
                    }
                )
                response = client.messages.create(
                    max_tokens=2024,
                    model="claude-3-7-sonnet-20250219",
                    tools=tools,
                    messages=messages,
                )

                if len(response.content) == 1 and response.content[0].type == "text":
                    print(response.content[0].text)
                    process_query = False


def chat_loop():
    print("Type your questions or 'quit' to exit.")
    while True:
        try:
            query = input("\nQuery: ").strip()
            if query.lower() == "quit":
                break
            process_query(query)
            print("\n")
        except Exception as e:
            print(f"\nError: {str(e)}")
