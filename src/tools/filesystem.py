import os
import platform


MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024
MAX_SEARCH_RESULTS = 50
MAX_SEARCH_DEPTH = 6

ALLOWED_TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".json", ".yaml", ".yml", ".csv",
    ".log", ".ini", ".cfg", ".toml", ".xml", ".html", ".js",
    ".ts", ".sh", ".java", ".c", ".cpp", ".rs", ".go"
}


def _get_downloads_dir() -> str:
    home = os.path.expanduser("~")
    return os.path.join(home, "Downloads")


def _resolve_within_home(path: str):
    real_path = os.path.realpath(os.path.expanduser(path))
    home_dir = os.path.realpath(os.path.expanduser("~"))
    if real_path == home_dir or real_path.startswith(home_dir + os.sep):
        return real_path
    return None


def find_files(query: str, directory: str = None, extension: str = None) -> str:
    try:
        if not query or not query.strip():
            return "Error: 'query' parameter cannot be empty."

        raw_dir = directory if directory else _get_downloads_dir()
        search_dir_real = _resolve_within_home(raw_dir)

        if search_dir_real is None:
            return "Error: access denied. Search is restricted to the user's home directory tree."

        if not os.path.isdir(search_dir_real):
            return f"Error: directory '{raw_dir}' does not exist or is not accessible."

        query_lower = query.lower()
        ext_lower = extension.lower().lstrip(".") if extension else None
        matches = []
        base_depth = search_dir_real.rstrip(os.sep).count(os.sep)

        for root, dirs, files in os.walk(search_dir_real, topdown=True):
            current_depth = root.rstrip(os.sep).count(os.sep) - base_depth
            if current_depth >= MAX_SEARCH_DEPTH:
                dirs[:] = []
                continue

            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for filename in files:
                if filename.startswith("."):
                    continue
                if query_lower not in filename.lower():
                    continue
                if ext_lower and not filename.lower().endswith("." + ext_lower):
                    continue
                matches.append(os.path.join(root, filename))
                if len(matches) >= MAX_SEARCH_RESULTS:
                    break

            if len(matches) >= MAX_SEARCH_RESULTS:
                break

        if not matches:
            return f"No files matching '{query}' were found in '{search_dir_real}'."

        result_lines = [f"Found {len(matches)} file(s) matching '{query}' in '{search_dir_real}':"]
        result_lines.extend(matches)
        return "\n".join(result_lines)

    except PermissionError:
        return f"Error: permission denied while accessing '{directory or _get_downloads_dir()}'."
    except Exception as e:
        return f"Error while searching for files: {str(e)}"


def read_file_text(file_path: str, max_lines: int = 150) -> str:
    try:
        if not file_path or not file_path.strip():
            return "Error: 'file_path' parameter cannot be empty."

        real_path = _resolve_within_home(file_path)
        if real_path is None:
            return "Error: access denied. File reading is restricted to the user's home directory tree."

        if not os.path.isfile(real_path):
            return f"Error: '{file_path}' is not a valid file or does not exist."

        _, ext = os.path.splitext(real_path)
        if ext.lower() not in ALLOWED_TEXT_EXTENSIONS:
            return f"Error: file extension '{ext}' is not allowed for text reading."

        file_size = os.path.getsize(real_path)
        if file_size > MAX_FILE_SIZE_BYTES:
            return f"Error: file too large ({file_size} bytes). Maximum allowed is {MAX_FILE_SIZE_BYTES} bytes."

        safe_max_lines = max(1, min(max_lines, 1000))
        lines = []
        truncated = False

        with open(real_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= safe_max_lines:
                    truncated = True
                    break
                lines.append(line.rstrip("\n"))

        content = "\n".join(lines)
        if truncated:
            content += f"\n\n[Output truncated after {safe_max_lines} lines]"

        if not content.strip():
            return f"The file '{file_path}' is empty."

        return content

    except PermissionError:
        return f"Error: permission denied while reading '{file_path}'."
    except UnicodeDecodeError:
        return f"Error: could not decode '{file_path}' as text."
    except Exception as e:
        return f"Error while reading file: {str(e)}"

def list_directory(directory: str = None) -> str:
    try:
        raw_dir = directory if directory else _get_downloads_dir()
        dir_real = _resolve_within_home(raw_dir)

        if dir_real is None:
            return "Error: access denied. Directory listing is restricted to the user's home directory tree."

        if not os.path.isdir(dir_real):
            return f"Error: '{raw_dir}' is not a directory or does not exist."

        entries = os.listdir(dir_real)
        if not entries:
            return f"The directory '{dir_real}' is empty."

        items = []
        for entry in sorted(entries):
            if entry.startswith("."):
                continue
            full_path = os.path.join(dir_real, entry)
            is_dir = os.path.isdir(full_path)
            prefix = "[DIR] " if is_dir else "[FILE]"
            items.append(f"{prefix} {entry}")

        return f"Contents of '{dir_real}':\n" + "\n".join(items[:100])

    except PermissionError:
        return f"Error: permission denied while accessing '{directory or _get_downloads_dir()}'."
    except Exception as e:
        return f"Error while listing directory: {str(e)}"