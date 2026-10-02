import os
import re


MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024
MAX_SEARCH_RESULTS = 50
MAX_SEARCH_DEPTH = 6
IGNORED_DIRECTORIES = {".git", "__pycache__", "node_modules", ".venv", "target", "build"}

ALLOWED_TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".json", ".yaml", ".yml", ".csv",
    ".log", ".ini", ".cfg", ".toml", ".xml", ".html", ".js",
    ".ts", ".sh", ".java", ".c", ".cpp", ".rs", ".go"
}


def _workspace_root() -> str:
    return os.path.realpath(os.getcwd())


def _resolve_within_workspace(path: str):
    workspace = _workspace_root()
    candidate = os.path.expanduser(path or ".")
    real_path = os.path.realpath(candidate if os.path.isabs(candidate) else os.path.join(workspace, candidate))
    try:
        if os.path.commonpath((workspace, real_path)) == workspace:
            return real_path
    except ValueError:
        pass
    return None


def find_files(query: str, directory: str = None, extension: str = None) -> str:
    try:
        if not query or not query.strip():
            return "Error: 'query' parameter cannot be empty."

        raw_dir = directory if directory else "."
        search_dir_real = _resolve_within_workspace(raw_dir)

        if search_dir_real is None:
            return "Error: access denied. Search is restricted to the current workspace."

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

            dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES and not d.startswith(".")]

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
        return f"Error: permission denied while accessing '{directory or os.getcwd()}'."
    except Exception as e:
        return f"Error while searching for files: {str(e)}"


def read_file_text(path: str = None, start_line: int = None, end_line: int = None,
                   max_lines: int = 150, file_path: str = None) -> str:
    try:
        path = path or file_path
        if not path or not path.strip():
            return "Error: 'path' parameter cannot be empty."

        real_path = _resolve_within_workspace(path)
        if real_path is None:
            return "Error: access denied. File reading is restricted to the current workspace."

        if not os.path.isfile(real_path):
            return f"Error: '{path}' is not a valid file or does not exist."

        _, ext = os.path.splitext(real_path)
        if ext.lower() not in ALLOWED_TEXT_EXTENSIONS:
            return f"Error: file extension '{ext}' is not allowed for text reading."

        file_size = os.path.getsize(real_path)
        if file_size > MAX_FILE_SIZE_BYTES:
            return f"Error: file too large ({file_size} bytes). Maximum allowed is {MAX_FILE_SIZE_BYTES} bytes."

        if start_line is not None and start_line < 1:
            return "Error: 'start_line' must be at least 1."
        if end_line is not None and end_line < 1:
            return "Error: 'end_line' must be at least 1."
        if start_line is not None and end_line is not None and end_line < start_line:
            return "Error: 'end_line' must not be smaller than 'start_line'."

        safe_max_lines = max(1, min(max_lines, 1000))
        first_line = start_line or 1
        requested_last_line = end_line if end_line is not None else first_line + safe_max_lines - 1
        last_line = min(requested_last_line, first_line + safe_max_lines - 1)
        lines = []
        truncated = False

        with open(real_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                line_number = i + 1
                if line_number < first_line:
                    continue
                if line_number > last_line:
                    truncated = line_number > last_line and requested_last_line > last_line
                    break
                lines.append(line.rstrip("\n"))

        content = "\n".join(lines)
        if truncated:
            content += f"\n\n[Output truncated after {len(lines)} lines]"

        if not content.strip():
            return f"The file '{path}' is empty."

        return content

    except PermissionError:
        return f"Error: permission denied while reading '{path}'."
    except UnicodeDecodeError:
        return f"Error: could not decode '{path}' as text."
    except Exception as e:
        return f"Error while reading file: {str(e)}"

def list_directory(directory: str = None) -> str:
    try:
        raw_dir = directory if directory else "."
        dir_real = _resolve_within_workspace(raw_dir)

        if dir_real is None:
            return "Error: access denied. Directory listing is restricted to the current workspace."

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
        return f"Error: permission denied while accessing '{directory or os.getcwd()}'."
    except Exception as e:
        return f"Error while listing directory: {str(e)}"


def search_codebase(query: str, path: str = ".") -> str:
    """Search workspace text files with a regular expression and report file lines."""
    try:
        if not query or not query.strip():
            return "Error: 'query' parameter cannot be empty."
        search_root = _resolve_within_workspace(path)
        if search_root is None:
            return "Error: access denied. Code search is restricted to the current workspace."
        if not os.path.isdir(search_root):
            return f"Error: '{path}' is not a directory or does not exist."
        try:
            pattern = re.compile(query)
        except re.error as exc:
            return f"Error: invalid regular expression: {exc}"

        matches = []
        for root, dirs, files in os.walk(search_root, topdown=True):
            dirs[:] = [directory for directory in dirs if directory not in IGNORED_DIRECTORIES]
            for filename in files:
                full_path = os.path.join(root, filename)
                if os.path.getsize(full_path) > MAX_FILE_SIZE_BYTES:
                    continue
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as handle:
                        for line_number, line in enumerate(handle, start=1):
                            if pattern.search(line):
                                relative_path = os.path.relpath(full_path, _workspace_root()).replace(os.sep, "/")
                                matches.append(f"{relative_path}:{line_number}: {line.rstrip()}")
                                if len(matches) >= MAX_SEARCH_RESULTS:
                                    return "\n".join(matches)
                except (OSError, UnicodeError):
                    continue
        return "\n".join(matches) if matches else f"No matches found for '{query}'."
    except PermissionError:
        return f"Error: permission denied while searching '{path}'."
    except Exception as exc:
        return f"Error while searching codebase: {exc}"