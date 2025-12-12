"""
Tool Definitions
================

Tool schemas for the LLM to use.
"""

TOOLS = [
    # Bash command execution
    {
        "name": "bash",
        "description": "Execute a bash command. Use this to run any shell command including npm, git, python, curl, etc. Commands run in the workspace directory by default.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Optional working directory (relative to /workspace or absolute path)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 120)"
                }
            },
            "required": ["command"]
        }
    },
    
    # File reading
    {
        "name": "read_file",
        "description": "Read the contents of a file. Returns the full file content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file (relative to /workspace or absolute)"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Optional start line (1-indexed)"
                },
                "end_line": {
                    "type": "integer",
                    "description": "Optional end line (1-indexed, inclusive)"
                }
            },
            "required": ["path"]
        }
    },
    
    # File writing
    {
        "name": "write_file",
        "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does. Creates parent directories automatically.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file (relative to /workspace or absolute)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    },
    
    # File editing
    {
        "name": "edit_file",
        "description": "Edit an existing file by replacing specific content. Use for targeted edits rather than rewriting entire files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file"
                },
                "old_content": {
                    "type": "string",
                    "description": "The exact content to find and replace"
                },
                "new_content": {
                    "type": "string",
                    "description": "The new content to replace with"
                }
            },
            "required": ["path", "old_content", "new_content"]
        }
    },
    
    # Directory listing
    {
        "name": "list_directory",
        "description": "List files and directories in a path. Returns file names, types, and sizes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory (default: current workspace)"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "If true, list recursively (default: false)"
                }
            },
            "required": []
        }
    },
    
    # File search
    {
        "name": "search_files",
        "description": "Search for files by name pattern or search within file contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern for file names (e.g., '*.py', 'src/**/*.ts')"
                },
                "content": {
                    "type": "string",
                    "description": "Search for this text within files"
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: workspace)"
                }
            },
            "required": []
        }
    },
    
    # Browser navigation
    {
        "name": "browser_navigate",
        "description": "Navigate to a URL in headless Chrome browser. Opens a new page if not already open.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to navigate to"
                },
                "wait_for": {
                    "type": "string",
                    "description": "Optional CSS selector to wait for before returning"
                }
            },
            "required": ["url"]
        }
    },
    
    # Browser screenshot
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current browser page. Returns the path to the saved image.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename for the screenshot (default: screenshot-{timestamp}.png)"
                },
                "full_page": {
                    "type": "boolean",
                    "description": "If true, capture the full page (default: false, viewport only)"
                }
            },
            "required": []
        }
    },
    
    # Browser click
    {
        "name": "browser_click",
        "description": "Click an element on the current page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the element to click"
                }
            },
            "required": ["selector"]
        }
    },
    
    # Browser fill
    {
        "name": "browser_fill",
        "description": "Type text into an input field.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the input element"
                },
                "text": {
                    "type": "string",
                    "description": "Text to type into the input"
                }
            },
            "required": ["selector", "text"]
        }
    },
    
    # Browser evaluate JavaScript
    {
        "name": "browser_evaluate",
        "description": "Execute JavaScript in the browser context. Returns the result of the expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "JavaScript code to execute"
                }
            },
            "required": ["script"]
        }
    },
]
