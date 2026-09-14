from tools.time import get_time
from tools.filesystem import find_files, read_file_text, list_directory
from tools.search import web_search

TOOLS = {
    "get_time": get_time,
    "find_files": find_files,
    "read_file_text": read_file_text,
    "list_directory": list_directory,
    "web_search": web_search
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Returns the current local time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "Searches for files by name inside the user's home directory tree. Defaults to the Downloads folder if no directory is provided.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Part of the file name to search for."
                    },
                    "directory": {
                        "type": "string",
                        "description": "Absolute path of the directory to search in. Defaults to the user's Downloads folder if omitted."
                    },
                    "extension": {
                        "type": "string",
                        "description": "File extension to filter results by, without the dot (e.g. 'pdf', 'py')."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_text",
            "description": "Reads the text content of a file (e.g. .txt, .md, .py) located inside the user's home directory tree, truncated to a maximum number of lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or user-relative path to the text file to read."
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum number of lines to read from the file. Defaults to 150."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Performs a web search and returns a list of titles, snippets and links for the given query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to return. Defaults to 3."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists the files and folders inside a given directory. Defaults to the Downloads folder if omitted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Path to the directory. Defaults to the user's Downloads folder if omitted."
                    }
                },
                "required": []
            }
        }
    }
]