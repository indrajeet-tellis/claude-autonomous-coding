#!/usr/bin/env python3
"""
Autonomous Coding Agent with Claude Agent SDK
==============================================

Agent that uses the official Claude Agent SDK for enhanced streaming output,
built-in tools, and better conversation management.

Integrates with the dashboard API for logging, progress, and screenshots.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import httpx
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Claude Agent SDK imports
try:
    from claude_agent_sdk import (
        query,
        ClaudeAgentOptions,
        AssistantMessage,
        UserMessage,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
    )
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Warning: claude-agent-sdk not installed, falling back to custom loop")

console = Console()

# Configuration
WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
API_URL = os.environ.get("API_URL", "http://backend:8000")
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "500"))
AGENT_HEADLESS = os.environ.get("AGENT_HEADLESS", "false").lower() == "true"


# ============================================================================
# Dashboard API Helpers
# ============================================================================

async def log_to_api(task_id: str, level: str, message: str, tool: str = None):
    """Send log to dashboard API."""
    if task_id == "local":
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{API_URL}/api/logs",
                json={
                    "taskId": task_id,
                    "level": level,
                    "message": message[:2000],  # Truncate long messages
                    "tool": tool,
                },
                timeout=5.0
            )
    except Exception as e:
        console.print(f"[dim]Failed to send log to API: {e}[/dim]")


async def update_task_status(task_id: str, status: str, progress: int = None):
    """Update task status in dashboard via internal endpoint."""
    if task_id == "local":
        return
    try:
        async with httpx.AsyncClient() as client:
            data = {"status": status}
            if progress is not None:
                data["progress"] = progress
            await client.patch(
                f"{API_URL}/api/tasks/{task_id}/status",
                json=data,
                timeout=5.0
            )
    except Exception as e:
        console.print(f"[dim]Failed to update task status: {e}[/dim]")


async def register_screenshot(task_id: str, filename: str):
    """Register screenshot with dashboard."""
    if task_id == "local":
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{API_URL}/api/screenshots",
                params={"task_id": task_id, "filename": filename},
                timeout=5.0
            )
    except Exception:
        pass


# ============================================================================
# Task Loading
# ============================================================================

def load_task() -> dict:
    """Load task definition from workspace."""
    task_file = WORKSPACE / "task.yaml"
    
    if not task_file.exists():
        return {
            "id": "local",
            "name": "Interactive Mode",
            "description": "No task.yaml found. Running in interactive mode.",
            "success_criteria": [],
            "preferences": {},
            "workspace": str(WORKSPACE)
        }
    
    with open(task_file) as f:
        task = yaml.safe_load(f)
    
    if "id" not in task:
        task["id"] = "local"
    
    # Set workspace path
    if "workspace" in task:
        task["workspace_path"] = Path(task["workspace"])
    else:
        task["workspace_path"] = WORKSPACE
    
    return task


def format_task_prompt(task: dict) -> str:
    """Format the task into a prompt for the SDK."""
    prompt = f"""## Task: {task.get('name', 'Unnamed Task')}

{task.get('description', 'No description provided.')}

### Success Criteria
"""
    criteria = task.get('success_criteria', [])
    if criteria:
        for i, criterion in enumerate(criteria, 1):
            prompt += f"{i}. {criterion}\n"
    else:
        prompt += "- Complete the task as described\n"
    
    prefs = task.get('preferences', {})
    if prefs:
        prompt += "\n### Preferences\n"
        for key, value in prefs.items():
            prompt += f"- {key}: {value}\n"
    
    prompt += f"""
### Instructions
Execute this task autonomously. Take action immediately without asking for permission.
Work in the directory: {task.get('workspace_path', WORKSPACE)}
"""
    return prompt


# ============================================================================
# Claude Agent SDK Runner
# ============================================================================

async def process_sdk_message(task_id: str, message, iteration: int):
    """Process a message from the Claude Agent SDK and log to dashboard."""
    
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                # Claude's text response
                console.print(Panel(Markdown(block.text[:1000]), title="Claude", border_style="green"))
                await log_to_api(task_id, "INFO", block.text)
                
            elif isinstance(block, ToolUseBlock):
                # Tool being used
                tool_info = f"Using {block.name}"
                if hasattr(block, 'input') and block.input:
                    # Show truncated input
                    input_str = json.dumps(block.input)[:200]
                    tool_info += f": {input_str}"
                
                console.print(f"[yellow]🔧 {tool_info}[/yellow]")
                await log_to_api(task_id, "TOOL", f"Using tool: {block.name}", block.name)
                
            elif isinstance(block, ToolResultBlock):
                # Tool result
                result_preview = str(block.output)[:300] if hasattr(block, 'output') else "..."
                console.print(f"[dim]   → {result_preview}[/dim]")
                
    elif isinstance(message, ResultMessage):
        # Task completed
        console.print("[bold green]✓ Task completed![/bold green]")
        await update_task_status(task_id, "COMPLETED", 100)
        await log_to_api(task_id, "INFO", "Task completed successfully!")
        return True
    
    # Check for any thinking blocks (extended thinking)
    if hasattr(message, 'content'):
        for block in message.content:
            if hasattr(block, 'type') and block.type == 'thinking':
                thinking_text = getattr(block, 'thinking', '')[:500]
                console.print(f"[dim magenta]💭 Thinking: {thinking_text}...[/dim magenta]")
                await log_to_api(task_id, "DEBUG", f"Thinking: {thinking_text[:200]}")
    
    return False


async def run_with_sdk(task: dict):
    """Run the agent using Claude Agent SDK."""
    task_id = task.get("id", "local")
    workspace = task.get("workspace_path", WORKSPACE)
    
    console.print(Panel.fit(
        "[bold cyan]🚀 Claude Agent SDK Mode[/bold cyan]\n"
        f"Workspace: {workspace}\n"
        f"Max Iterations: {MAX_ITERATIONS}",
        border_style="cyan"
    ))
    
    # SDK options with built-in tools
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash", "Glob", "Grep"],
        permission_mode='acceptEdits',  # Auto-accept file changes
        cwd=str(workspace),
        max_turns=MAX_ITERATIONS,
    )
    
    prompt = format_task_prompt(task)
    
    await update_task_status(task_id, "RUNNING", 0)
    await log_to_api(task_id, "INFO", "Agent started with Claude Agent SDK")
    
    iteration = 0
    completed = False
    
    try:
        async for message in query(prompt=prompt, options=options):
            iteration += 1
            
            # Update progress
            progress_pct = min(int((iteration / MAX_ITERATIONS) * 100), 99)
            await update_task_status(task_id, "RUNNING", progress_pct)
            
            # Process and log the message
            completed = await process_sdk_message(task_id, message, iteration)
            
            if completed:
                break
                
            if iteration >= MAX_ITERATIONS:
                console.print(f"[yellow]Reached max iterations ({MAX_ITERATIONS})[/yellow]")
                await update_task_status(task_id, "PAUSED", progress_pct)
                break
                
    except Exception as e:
        console.print(f"[red]Error during SDK execution: {e}[/red]")
        await log_to_api(task_id, "ERROR", str(e))
        await update_task_status(task_id, "FAILED", 0)
        raise
    
    if not completed:
        await log_to_api(task_id, "INFO", f"Agent stopped after {iteration} iterations")


# ============================================================================
# Fallback: Custom Loop (when SDK not available)
# ============================================================================

async def run_with_custom_loop(task: dict):
    """Fallback: Run with custom anthropic SDK loop (original implementation)."""
    # Import the original modules
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from client import create_client, call_llm
    from tools import TOOLS, execute_tool
    from prompts import get_system_prompt
    
    task_id = task.get("id", "local")
    
    console.print(Panel.fit(
        "[bold yellow]⚠ Fallback Mode (Custom Loop)[/bold yellow]\n"
        "Claude Agent SDK not available",
        border_style="yellow"
    ))
    
    await update_task_status(task_id, "RUNNING", 0)
    
    client = create_client()
    prompt = format_task_prompt(task)
    messages = [{"role": "user", "content": prompt}]
    
    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1
        progress_pct = min(int((iteration / MAX_ITERATIONS) * 100), 99)
        await update_task_status(task_id, "RUNNING", progress_pct)
        
        console.print(f"\n[bold blue]━━━ Iteration {iteration}/{MAX_ITERATIONS} ━━━[/bold blue]")
        
        try:
            response = await call_llm(client, messages, TOOLS)
            
            # Process response
            assistant_content = []
            tool_calls = []
            text_response = ""
            
            for block in response.content:
                if block.type == "text":
                    text_response += block.text
                    assistant_content.append({"type": "text", "text": block.text})
                    console.print(Panel(Markdown(block.text[:500]), title="Agent", border_style="green"))
                    await log_to_api(task_id, "INFO", block.text[:500])
                elif block.type == "tool_use":
                    tool_calls.append(block)
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                    console.print(f"[yellow]🔧 Tool: {block.name}[/yellow]")
                    await log_to_api(task_id, "TOOL", f"Using tool: {block.name}", block.name)
            
            messages.append({"role": "assistant", "content": assistant_content})
            
            if tool_calls:
                tool_results = []
                for tool_call in tool_calls:
                    result = await execute_tool(tool_call.name, tool_call.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result
                    })
                messages.append({"role": "user", "content": tool_results})
                continue
            
            # Check for completion
            if response.stop_reason == "end_turn":
                completion_signals = ["task complete", "successfully completed", "all done"]
                if any(s in text_response.lower() for s in completion_signals):
                    await update_task_status(task_id, "COMPLETED", 100)
                    console.print("[bold green]✓ Task completed![/bold green]")
                    break
                    
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            await log_to_api(task_id, "ERROR", str(e))
            await asyncio.sleep(3)
            continue
    
    if iteration >= MAX_ITERATIONS:
        await update_task_status(task_id, "PAUSED", 99)


# ============================================================================
# Main Entry Point
# ============================================================================

async def run_autonomous_agent():
    """Main agent entry point."""
    console.print(Panel.fit(
        "[bold magenta]🤖 Autonomous Coding Agent[/bold magenta]\n"
        f"SDK Available: {SDK_AVAILABLE}\n"
        f"Mode: {'Headless' if AGENT_HEADLESS else 'GUI (VNC)'}",
        border_style="magenta"
    ))
    
    task = load_task()
    
    console.print(f"\n[bold]Task:[/bold] {task.get('name', 'Unknown')}")
    console.print(f"[bold]Workspace:[/bold] {task.get('workspace_path', WORKSPACE)}")
    
    if SDK_AVAILABLE:
        await run_with_sdk(task)
    else:
        await run_with_custom_loop(task)
    
    console.print("\n[bold]Agent session ended.[/bold]")


def main():
    """Entry point."""
    try:
        asyncio.run(run_autonomous_agent())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
