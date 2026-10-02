from tools.time import get_time
from tools.filesystem import find_files, read_file_text, list_directory, search_codebase
from tools.search import web_search
from tools.canvas import get_grades, get_weekly_assignments
from tools.system import check_system_health
from integrations.microsoft import (
    authenticate_microsoft,
    list_emails,
    move_email,
    read_email,
    search_emails,
)

TOOLS = {
    "get_time": get_time,
    "find_files": find_files,
    "read_file_text": read_file_text,
    "list_directory": list_directory,
    "search_codebase": search_codebase,
    "web_search": web_search,
    "get_grades": get_grades,
    "get_weekly_assignments": get_weekly_assignments,
    "check_system_health": check_system_health,
    "authenticate_microsoft": authenticate_microsoft,
    "list_emails": list_emails,
    "read_email": read_email,
    "search_emails": search_emails,
    "move_email": move_email,
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
            "name": "get_grades",
            "description": "Retrieves the user's Canvas grades for courses whose course code starts with the requested prefix. Use this when the user asks to see grades or notes from Canvas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_prefix": {
                        "type": "string",
                        "description": "Course-code prefix to filter, such as 'FA26'. Defaults to 'FA26'."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weekly_assignments",
            "description": "Lists unfinished Canvas assignments due from today through Saturday of the current Sunday-to-Saturday week. Use this for weekly homework, lessons, tasks, or to-do list requests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_prefix": {
                        "type": "string",
                        "description": "Course-code prefix to filter, such as 'FA26'. Defaults to 'FA26'."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_system_health",
            "description": "Checks CPU, RAM, and system storage usage. Use this when the user asks to check, monitor, diagnose, or inspect system resources. Critical results use a UI safety marker that the chat displays in red.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "authenticate_microsoft",
            "description": "Authenticate Ultron with the user's Microsoft Outlook account using the normal browser login.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_emails",
            "description": "List recent Outlook emails and return each message_id. Use this before read_email when the user identifies an email by latest/recent, sender, subject, or other natural language instead of a Graph message ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "description": "Maximum messages to return, up to 100."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_email",
            "description": "Read the contents and metadata of a specific Outlook email. message_id must be the real Microsoft Graph message ID returned by list_emails or search_emails, never a subject, sender name, email address, or other natural-language identifier. If the user did not provide a Graph ID, call search_emails or list_emails first, then call read_email with the matching message_id. If multiple messages match, ask the user to choose unless latest/date clearly selects one.",
            "parameters": {
                "type": "object",
                "properties": {"message_id": {"type": "string", "description": "Microsoft Graph message ID."}},
                "required": ["message_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Search the user's Outlook mailbox for emails matching a subject, sender, email address, keywords, or date-related query. Use this before read_email when the user names an email naturally; the results include the real message_id needed by read_email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Sender, subject, keyword, or other Outlook search text."},
                    "max_results": {"type": "integer", "description": "Maximum messages to return, up to 100."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_email",
            "description": "Move an Outlook email to a mailbox folder. This changes the email's location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Microsoft Graph message ID."},
                    "destination_folder": {
                        "type": "string",
                        "enum": ["Inbox", "Archive", "Drafts", "Sent Items", "Junk Email"],
                        "description": "Approved existing mailbox folder."
                    }
                },
                "required": ["message_id", "destination_folder"]
            }
        }
    }
]