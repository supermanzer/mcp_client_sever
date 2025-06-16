"""
arXiv Research Paper Management Server

This module implements a Model Context Protocol (MCP) server that provides tools and resources
for searching, storing, and managing academic papers from arXiv. It offers functionality to:
- Search for papers by topic
- Store paper metadata in a structured format
- Extract paper information
- Browse papers by research topics
- Generate research summaries

The server uses FastMCP to expose its functionality and organizes papers into topic-based
directories, storing metadata in JSON format.

Features:
    - arXiv integration for paper searches
    - Topic-based paper organization
    - JSON-based metadata storage
    - Markdown-formatted paper listings
    - Paper information extraction
    - Research summary generation

Dependencies:
    - arxiv: For accessing the arXiv API
    - mcp.server.fastmcp: For MCP server implementation
    - json: For metadata storage
    - os: For file system operations

Directory Structure:
    papers/
        topic_name/
            papers_info.json
"""

import arxiv
import json
import os
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("research")


PAPER_DIR = "papers"


@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    List all available research topic folders and format them as a markdown list.
    
    Returns:
        str: Markdown-formatted string containing:
            - List of available research topics
            - Instructions for accessing papers in a topic
            - Message if no topics are available
    """
    folders = []

    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, 'papers_info.json')
                if os.path.exists(papers_file):
                    folders.append(topic_dir)

    content = "# Available Topics\n\n"
    if folders:
        # Using join() with template strings to create a formatted list
        content += '\n'.join(f'- {folder.replace("_", " ").title()}' for folder in folders)
        content += f"\nUse @{folders[0]} to access papers in that topic.\n"
    else:
        content += "No research topics available yet."
    
    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Retrieve and format information about all papers in a specific topic.
    
    Args:
        topic: The research topic to retrieve papers for
        
    Returns:
        str: Markdown-formatted string containing:
            - Topic title
            - Total number of papers
            - Detailed information for each paper including:
                - Title
                - Paper ID
                - Authors
                - Publication date
                - PDF URL
                - Summary
                
    Note:
        Papers are stored in topic-specific directories with metadata in papers_info.json
    """
    PAPER_TEMPLATE="""
## {title}
- **Paper ID**: {id}
- **Authors**: {authors}
- **Publiished**: {published}
- **PDF URL**: {pdf_url}
### Summary
{summary}
"""
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")

    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}\nTry searching for papers on this topic"
    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)
        content = f"# Papers on {topic.replace('_', " ")}\n\nTotal papers: {len(papers_data)}\n\n"

        for paper_id, paper_info, in papers_data.items():
            content += PAPER_TEMPLATE.format(
                title=paper_info.get('title', ''),
                id=paper_id,
                authors=', '.join(paper_info.get('authors',[])),
                published=paper_info.get('published', ''),
                pdf_url=paper_info.get('pdf_url', ''),
                summary=paper_info.get('summary', '')
            )
            content += '\n\n'
        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\n.The file is corrupted"
    

@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """
    Generate a detailed prompt for searching and analyzing papers on a specific topic.
    
    This function creates a structured prompt that guides the search process and
    subsequent analysis of academic papers, ensuring comprehensive coverage of the
    research landscape.
    
    Args:
        topic: The research topic to investigate
        num_papers: Number of papers to include in the analysis (default: 5)
        
    Returns:
        str: A detailed prompt string that includes:
            - Search instructions
            - Analysis requirements
            - Summary structure guidelines
            - Synthesis requirements
    """
    return f"""Search for {num_papers} academic papers about '{topic}' using the search_papers tool. Follow these instructions:
    1. First, search for papers using search_papers(topic='{topic}', max_results={num_papers})
    2. For each paper found, extract and organize the following information:
       - Paper title
       - Authors
       - Publication date
       - Brief summary of the key findings
       - Main contributions or innovations
       - Methodologies used
       - Relevance to the topic '{topic}'
    
    3. Provide a comprehensive summary that includes:
       - Overview of the current state of research in '{topic}'
       - Common themes and trends across the papers
       - Key research gaps or areas for future investigation
       - Most impactful or influential papers in this area
    
    4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.
    
    Please present both detailed information about each paper and a high-level synthesis of the research landscape in {topic}."""




@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    
    This function searches arXiv for papers matching the given topic, downloads
    their metadata, and stores it in a topic-specific JSON file. It creates
    the necessary directory structure if it doesn't exist.
    
    Args:
        topic: The topic to search for papers about
        max_results: Maximum number of papers to retrieve (default: 5)
        
    Returns:
        List[str]: List of arXiv paper IDs found in the search
        
    Note:
        Papers are stored in: papers/<topic>/papers_info.json
        Each paper's metadata includes:
            - Title
            - Authors
            - Summary
            - PDF URL
            - Publication date
    """

    # Use arxiv to find the papers
    client = arxiv.Client()

    # Search for the most relevant articles matching the queried topic
    search = arxiv.Search(
        query=topic, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)

    # Create directory for this topic
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "papers_info.json")

    # Try to load existing papers info
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # Process each paper and add to papers_info
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }
        papers_info[paper.get_short_id()] = paper_info

    # Save updated papers_info to json file
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)

    print(f"Results are saved in: {file_path}")

    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for and extract information about a specific paper across all topics.
    
    This function searches through all topic directories to find metadata about
    a specific paper identified by its arXiv ID.
    
    Args:
        paper_id: The arXiv ID of the paper to look for
        
    Returns:
        str: JSON-formatted string containing the paper's metadata if found,
             or an error message if the paper is not found
        
    Note:
        The function searches all topic directories as a paper might be
        referenced in multiple research topics.
    """
 
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    return f"There's no saved information related to paper {paper_id}."

tools = [
    {
        "name": "search_papers",
        "description": "Search for papers on arXiv based on a topic and store their information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to search for"
                }, 
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to retrieve",
                    "default": 5
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "extract_info",
        "description": "Search for information about a specific paper across all topic directories.",
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {
                    "type": "string",
                    "description": "The ID of the paper to look for"
                }
            },
            "required": ["paper_id"]
        }
    }
]

mapping_tool_function = {
    "search_papers": search_papers,
    "extract_info": extract_info
}

def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """
    Execute a tool by name with the provided arguments.
    
    This function serves as a dispatcher for tool execution, handling various
    return types and formatting the output appropriately.
    
    Args:
        tool_name: Name of the tool to execute
        tool_args: Dictionary of arguments to pass to the tool
        
    Returns:
        str: Formatted result of the tool execution:
            - For None: Message indicating completion
            - For lists: Comma-separated string
            - For dicts: Formatted JSON string
            - For other types: String representation
    """
    
    result = mapping_tool_function[tool_name](**tool_args)

    if result is None:
        result = "The operation completed but didn't return any results."
        
    elif isinstance(result, list):
        result = ', '.join(result)
        
    elif isinstance(result, dict):
        # Convert dictionaries to formatted JSON strings
        result = json.dumps(result, indent=2)
    
    else:
        # For any other type, convert using str()
        result = str(result)
    return result


if __name__ == "__main__":
    mcp.run(transport='stdio')