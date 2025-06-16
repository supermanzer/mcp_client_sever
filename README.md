# MCP Research Assistant

An intelligent research assistant that combines the Model Context Protocol (MCP) with Anthropic's Claude API to help researchers search, organize, and analyze academic papers from arXiv.

## Features

- **Interactive Chat Interface**: Natural language interaction with the research assistant
- **arXiv Integration**: Search and retrieve papers directly from arXiv
- **Topic Organization**: Papers are automatically organized by research topics
- **Metadata Storage**: Structured storage of paper information in JSON format
- **Research Summaries**: Generate comprehensive research summaries across multiple papers
- **Multi-Server Architecture**: Supports multiple MCP servers with different tool sets
- **Asynchronous Operation**: Efficient handling of concurrent operations

## Requirements

- Python 3.7+
- Anthropic API key (stored in `.env` file)
- `server_config.json` for MCP server configurations
- Required Python packages (see Dependencies section)

## Installation

1. Clone the repository
2. Create a `.env` file with your Anthropic API key:
   ```
   API_KEY=your_anthropic_api_key_here
   ```
3. Create a `server_config.json` file with your MCP server configurations
4. Install the required dependencies

## Dependencies

- `anthropic`: Anthropic Claude API client
- `arxiv`: arXiv API client
- `mcp`: Model Context Protocol implementation
- `python-dotenv`: Environment variable management
- `nest-asyncio`: Asyncio support in interactive environments

## Project Structure

```
├── client.py           # MCP chatbot client implementation
├── server.py           # arXiv research paper management server
├── server_config.json  # Server configuration file
└── papers/            # Directory for storing paper information
    └── topic_name/    # Topic-specific directories
        └── papers_info.json  # Paper metadata storage
```

## Usage

1. Start the MCP server:
   ```bash
   python server.py
   ```

2. In a separate terminal, start the client:
   ```bash
   python client.py
   ```

3. Interact with the chatbot using natural language queries. Examples:
   - "Search for papers about quantum computing"
   - "Show me available research topics"
   - "Get information about paper [paper_id]"
   - "Summarize recent papers in machine learning"

## Available Tools

### Search Papers
- Search for papers on arXiv by topic
- Automatically store paper metadata
- Organize papers by research topics

### Extract Information
- Retrieve detailed information about specific papers
- Access paper metadata across all topics
- Get formatted paper summaries

### Browse Topics
- List available research topics
- View papers within each topic
- Access topic-specific summaries

## Features in Detail

### Paper Information Storage
Each paper's metadata includes:
- Title
- Authors
- Summary
- PDF URL
- Publication date

### Research Summaries
Generated summaries include:
- Overview of current research state
- Common themes and trends
- Key research gaps
- Impactful papers
- Methodologies used

### Error Handling
- Graceful handling of API errors
- Corruption detection in storage files
- Connection error management
- Automatic resource cleanup

## Architecture

The project uses a client-server architecture:

### Server (`server.py`)
- Implements MCP server functionality
- Manages paper storage and organization
- Provides tools for paper search and analysis
- Handles arXiv integration

### Client (`client.py`)
- Implements interactive chat interface
- Manages connections to MCP servers
- Integrates with Claude AI
- Coordinates tool usage
- Handles user interaction

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

[Specify your license here]
