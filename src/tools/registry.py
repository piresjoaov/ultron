from tools.time import get_time
from tools.filesystem import find_files, read_file_text, list_directory, search_codebase
from tools.search import web_search

TOOLS = {
    "get_time": get_time,
    "find_files": find_files,
    "read_file_text": read_file_text,
    "list_directory": list_directory,
    "search_codebase": search_codebase,
    "web_search": web_search
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Returns the current local time for the user. CRITICAL: ONLY use this for the user's local time. If the user asks for the time in a different city or country (e.g., Tokyo, London), DO NOT use this tool. You MUST use 'web_search' instead to find foreign times.",
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
            "description": "Searches for files by name in the current workspace. Use this to locate files before reading them; defaults to the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Part of the file name to search for."
                    },
                    "directory": {
                        "type": "string",
                        "description": "Workspace-relative or absolute directory path. Defaults to the current working directory."
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
            "description": "Reads a text or source file in the current workspace. Use start_line and end_line to inspect only the relevant section of a large file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative or absolute path to the text file."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Optional 1-based first line to return. Use this when reading a specific code region."
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Optional 1-based last line to return, inclusive."
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum number of lines to read from the file. Defaults to 150."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Searches source files in the current workspace for a string or regular expression. Use this to find a function definition, class, symbol, import, or error across the project before reading matching files. Automatically skips .git, __pycache__, node_modules, .venv, target, and build directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Literal text or regular expression to find, such as 'def handle_message' or 'TODO|FIXME'."
                    },
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative directory to search. Defaults to '.'."
                    }
                },
                "required": ["query"]
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
            "description": "Lists files and folders inside the current workspace or a workspace-relative directory. Defaults to the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Workspace-relative or absolute directory path. Defaults to the current working directory."
                    }
                },
                "required": []
            }
        }
    }
]