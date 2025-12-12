"""
Tool Executor
=============

Executes tools by name with given inputs.
No permission system - everything runs immediately.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any

SCREENSHOTS_DIR = Path("/app/screenshots")


def get_workspace() -> Path:
    """Get the current workspace path from environment."""
    return Path(os.environ.get("WORKSPACE", "/workspace"))


def resolve_path(path: str) -> Path:
    """Resolve a path relative to workspace if not absolute."""
    workspace = get_workspace()
    if not path:
        return workspace
    p = Path(path)
    if p.is_absolute():
        return p
    return workspace / p


async def execute_tool(name: str, inputs: dict) -> str:
    """
    Execute a tool by name with given inputs.
    
    Args:
        name: Tool name
        inputs: Tool input parameters
    
    Returns:
        String result of the tool execution
    """
    try:
        if name == "bash":
            return await execute_bash(inputs)
        elif name == "read_file":
            return await execute_read_file(inputs)
        elif name == "write_file":
            return await execute_write_file(inputs)
        elif name == "edit_file":
            return await execute_edit_file(inputs)
        elif name == "list_directory":
            return await execute_list_directory(inputs)
        elif name == "search_files":
            return await execute_search_files(inputs)
        elif name == "browser_navigate":
            return await execute_browser_navigate(inputs)
        elif name == "browser_screenshot":
            return await execute_browser_screenshot(inputs)
        elif name == "browser_click":
            return await execute_browser_click(inputs)
        elif name == "browser_fill":
            return await execute_browser_fill(inputs)
        elif name == "browser_evaluate":
            return await execute_browser_evaluate(inputs)
        else:
            return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error executing {name}: {str(e)}"


# ============================================================================
# Bash Execution
# ============================================================================

async def execute_bash(inputs: dict) -> str:
    """Execute a bash command."""
    command = inputs.get("command", "")
    working_dir = inputs.get("working_dir")
    timeout = inputs.get("timeout", 120)
    
    if not command:
        return "Error: No command provided"
    
    cwd = resolve_path(working_dir) if working_dir else WORKSPACE
    
    try:
        # Run command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd)
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        result = ""
        if stdout:
            result += stdout.decode('utf-8', errors='replace')
        if stderr:
            result += "\n[stderr]\n" + stderr.decode('utf-8', errors='replace')
        if process.returncode != 0:
            result += f"\n[exit code: {process.returncode}]"
        
        return result.strip() or "(no output)"
        
    except asyncio.TimeoutError:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# File Operations
# ============================================================================

async def execute_read_file(inputs: dict) -> str:
    """Read file contents."""
    path = resolve_path(inputs.get("path", ""))
    start_line = inputs.get("start_line")
    end_line = inputs.get("end_line")
    
    if not path.exists():
        return f"Error: File not found: {path}"
    
    try:
        content = path.read_text(encoding='utf-8', errors='replace')
        
        if start_line or end_line:
            lines = content.splitlines()
            start = (start_line - 1) if start_line else 0
            end = end_line if end_line else len(lines)
            content = '\n'.join(lines[start:end])
        
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


async def execute_write_file(inputs: dict) -> str:
    """Write content to a file."""
    path = resolve_path(inputs.get("path", ""))
    content = inputs.get("content", "")
    
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        path.write_text(content, encoding='utf-8')
        return f"Successfully wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


async def execute_edit_file(inputs: dict) -> str:
    """Edit a file with search/replace."""
    path = resolve_path(inputs.get("path", ""))
    old_content = inputs.get("old_content", "")
    new_content = inputs.get("new_content", "")
    
    if not path.exists():
        return f"Error: File not found: {path}"
    
    if not old_content:
        return "Error: old_content is required"
    
    try:
        content = path.read_text(encoding='utf-8')
        
        if old_content not in content:
            return f"Error: Could not find the specified content to replace in {path}"
        
        # Count occurrences
        count = content.count(old_content)
        
        # Replace
        new_file_content = content.replace(old_content, new_content)
        path.write_text(new_file_content, encoding='utf-8')
        
        return f"Successfully replaced {count} occurrence(s) in {path}"
    except Exception as e:
        return f"Error editing file: {str(e)}"


async def execute_list_directory(inputs: dict) -> str:
    """List directory contents."""
    path = resolve_path(inputs.get("path", ""))
    recursive = inputs.get("recursive", False)
    
    if not path.exists():
        return f"Error: Directory not found: {path}"
    
    if not path.is_dir():
        return f"Error: Not a directory: {path}"
    
    try:
        if recursive:
            items = list(path.rglob("*"))
        else:
            items = list(path.iterdir())
        
        result = []
        for item in sorted(items)[:100]:  # Limit to 100 items
            rel = item.relative_to(path) if path != WORKSPACE else item.relative_to(WORKSPACE)
            item_type = "d" if item.is_dir() else "f"
            size = item.stat().st_size if item.is_file() else 0
            result.append(f"[{item_type}] {rel} ({size} bytes)")
        
        if len(items) > 100:
            result.append(f"... and {len(items) - 100} more items")
        
        return '\n'.join(result) or "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


async def execute_search_files(inputs: dict) -> str:
    """Search for files."""
    pattern = inputs.get("pattern")
    content_search = inputs.get("content")
    path = resolve_path(inputs.get("path", ""))
    
    if not path.exists():
        return f"Error: Path not found: {path}"
    
    results = []
    
    try:
        if pattern:
            # Search by filename pattern
            matches = list(path.glob(pattern))[:50]
            for match in matches:
                results.append(str(match.relative_to(WORKSPACE)))
        
        if content_search:
            # Search within files
            for file_path in path.rglob("*"):
                if file_path.is_file() and file_path.stat().st_size < 1_000_000:  # Skip large files
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if content_search in content:
                            results.append(f"{file_path.relative_to(WORKSPACE)}")
                    except:
                        pass
                if len(results) >= 50:
                    break
        
        return '\n'.join(results) or "No matches found"
    except Exception as e:
        return f"Error searching: {str(e)}"


# ============================================================================
# Browser Automation (via Puppeteer CLI)
# ============================================================================

# Global browser state
_browser_page_url = None


async def _run_puppeteer_script(script: str) -> str:
    """Run a Puppeteer script and return the result."""
    # Create a temporary script file
    script_path = Path("/tmp/puppeteer_script.js")
    
    full_script = f"""
const puppeteer = require('puppeteer');

(async () => {{
    const browser = await puppeteer.launch({{
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }});
    const page = await browser.newPage();
    await page.setViewport({{ width: 1280, height: 800 }});
    
    try {{
        {script}
    }} catch (error) {{
        console.log('ERROR: ' + error.message);
    }} finally {{
        await browser.close();
    }}
}})();
"""
    
    script_path.write_text(full_script)
    
    try:
        process = await asyncio.create_subprocess_exec(
            'node', str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(WORKSPACE)
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=60
        )
        
        result = stdout.decode('utf-8', errors='replace')
        if stderr:
            result += "\n" + stderr.decode('utf-8', errors='replace')
        
        return result.strip()
    except asyncio.TimeoutError:
        return "Error: Browser operation timed out"
    except Exception as e:
        return f"Error: {str(e)}"


async def execute_browser_navigate(inputs: dict) -> str:
    """Navigate browser to URL."""
    global _browser_page_url
    
    url = inputs.get("url", "")
    wait_for = inputs.get("wait_for")
    
    if not url:
        return "Error: URL is required"
    
    wait_script = ""
    if wait_for:
        wait_script = f"await page.waitForSelector('{wait_for}');"
    
    script = f"""
        await page.goto('{url}', {{ waitUntil: 'networkidle0', timeout: 30000 }});
        {wait_script}
        console.log('Navigated to: {url}');
        console.log('Title: ' + await page.title());
    """
    
    _browser_page_url = url
    return await _run_puppeteer_script(script)


async def execute_browser_screenshot(inputs: dict) -> str:
    """Take a screenshot."""
    global _browser_page_url
    
    if not _browser_page_url:
        return "Error: No page loaded. Use browser_navigate first."
    
    filename = inputs.get("filename") or f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    full_page = inputs.get("full_page", False)
    
    # Ensure screenshots directory exists
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = SCREENSHOTS_DIR / filename
    
    script = f"""
        await page.goto('{_browser_page_url}', {{ waitUntil: 'networkidle0', timeout: 30000 }});
        await page.screenshot({{ 
            path: '{screenshot_path}',
            fullPage: {str(full_page).lower()}
        }});
        console.log('Screenshot saved to: {screenshot_path}');
    """
    
    return await _run_puppeteer_script(script)


async def execute_browser_click(inputs: dict) -> str:
    """Click an element."""
    global _browser_page_url
    
    if not _browser_page_url:
        return "Error: No page loaded. Use browser_navigate first."
    
    selector = inputs.get("selector", "")
    if not selector:
        return "Error: Selector is required"
    
    script = f"""
        await page.goto('{_browser_page_url}', {{ waitUntil: 'networkidle0', timeout: 30000 }});
        await page.waitForSelector('{selector}');
        await page.click('{selector}');
        console.log('Clicked: {selector}');
    """
    
    return await _run_puppeteer_script(script)


async def execute_browser_fill(inputs: dict) -> str:
    """Fill an input field."""
    global _browser_page_url
    
    if not _browser_page_url:
        return "Error: No page loaded. Use browser_navigate first."
    
    selector = inputs.get("selector", "")
    text = inputs.get("text", "")
    
    if not selector:
        return "Error: Selector is required"
    
    script = f"""
        await page.goto('{_browser_page_url}', {{ waitUntil: 'networkidle0', timeout: 30000 }});
        await page.waitForSelector('{selector}');
        await page.type('{selector}', '{text}');
        console.log('Filled {selector} with text');
    """
    
    return await _run_puppeteer_script(script)


async def execute_browser_evaluate(inputs: dict) -> str:
    """Evaluate JavaScript in browser."""
    global _browser_page_url
    
    if not _browser_page_url:
        return "Error: No page loaded. Use browser_navigate first."
    
    user_script = inputs.get("script", "")
    if not user_script:
        return "Error: Script is required"
    
    # Escape the script for embedding
    escaped_script = user_script.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    
    script = f"""
        await page.goto('{_browser_page_url}', {{ waitUntil: 'networkidle0', timeout: 30000 }});
        const result = await page.evaluate(() => {{
            {escaped_script}
        }});
        console.log('Result:', JSON.stringify(result, null, 2));
    """
    
    return await _run_puppeteer_script(script)
