#!/usr/bin/env python3
"""
Autonomous Coding Agent (Dashboard Version)
============================================

Agent that integrates with the dashboard API for logging, progress, and screenshots.
Supports hybrid Chrome mode (GUI/headless toggle).
"""

import asyncio
import json
import os
import sys
import httpx
from pathlib import Path
from typing import Optional
from datetime import datetime

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from client import create_client, call_llm
from tools import TOOLS, execute_tool
from prompts import get_system_prompt

console = Console()

# Configuration
WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
API_URL = os.environ.get("API_URL", "http://backend:8000")
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "500"))
AUTO_CONTINUE_DELAY = int(os.environ.get("AUTO_CONTINUE_DELAY", "3"))
AGENT_HEADLESS = os.environ.get("AGENT_HEADLESS", "false").lower() == "true"


async def log_to_api(task_id: str, level: str, message: str, tool: str = None):
    """Send log to dashboard API."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{API_URL}/api/logs",
                json={
                    "taskId": task_id,
                    "level": level,
                    "message": message,
                    "tool": tool,
                },
                timeout=5.0
            )
    except Exception as e:
        console.print(f"[dim]Failed to send log to API: {e}[/dim]")


async def update_task_status(task_id: str, status: str, progress: int = None):
    """Update task status in dashboard via internal endpoint (no auth required)."""
    if task_id == "local":
        return  # Skip API calls for local tasks
    
    try:
        async with httpx.AsyncClient() as client:
            data = {"status": status}
            if progress is not None:
                data["progress"] = progress
            response = await client.patch(
                f"{API_URL}/api/tasks/{task_id}/status",
                json=data,
                timeout=5.0
            )
            if response.status_code == 200:
                console.print(f"[dim]Task status updated to: {status}[/dim]")
            else:
                console.print(f"[yellow]Failed to update status: {response.status_code}[/yellow]")
    except Exception as e:
        console.print(f"[dim]Failed to update task status: {e}[/dim]")


async def register_screenshot(task_id: str, filename: str):
    """Register screenshot with dashboard."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{API_URL}/api/screenshots",
                params={"task_id": task_id, "filename": filename},
                timeout=5.0
            )
    except Exception:
        pass


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
    
    # Add default id if not present
    if "id" not in task:
        task["id"] = "local"
    
    # Set workspace path (use task-specific workspace if specified)
    if "workspace" in task:
        task["workspace_path"] = Path(task["workspace"])
    else:
        task["workspace_path"] = WORKSPACE
    
    return task


def load_progress() -> dict:
    """Load progress from previous sessions."""
    progress_file = WORKSPACE / ".agent_progress.json"
    
    if not progress_file.exists():
        return {
            "iteration": 0,
            "completed_steps": [],
            "current_phase": "starting",
            "notes": []
        }
    
    with open(progress_file) as f:
        return json.load(f)


def save_progress(progress: dict) -> None:
    """Save progress for future sessions."""
    progress_file = WORKSPACE / ".agent_progress.json"
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def format_task_prompt(task: dict, progress: dict) -> str:
    """Format the task into a prompt for the agent."""
    prompt = f"""## Current Task

**Name:** {task.get('name', 'Unnamed Task')}

**Description:**
{task.get('description', 'No description provided.')}

**Success Criteria:**
"""
    
    criteria = task.get('success_criteria', [])
    if criteria:
        for i, criterion in enumerate(criteria, 1):
            prompt += f"{i}. {criterion}\n"
    else:
        prompt += "- Complete the task as described\n"
    
    prefs = task.get('preferences', {})
    if prefs:
        prompt += "\n**Preferences:**\n"
        for key, value in prefs.items():
            prompt += f"- {key}: {value}\n"
    
    if progress.get('notes'):
        prompt += "\n**Previous Session Notes:**\n"
        for note in progress['notes'][-5:]:
            prompt += f"- {note}\n"
    
    prompt += f"\n**Current Phase:** {progress.get('current_phase', 'starting')}"
    prompt += f"\n**Iteration:** {progress.get('iteration', 0) + 1}"
    prompt += f"\n**Chrome Mode:** {'Headless' if AGENT_HEADLESS else 'GUI (visible in VNC)'}"
    
    prompt += """

## Instructions

You are an autonomous coding agent. Execute the task above without asking for permission.
Take action immediately. When you complete a step, move to the next one.
If you encounter an error, fix it and continue.

Begin by analyzing what needs to be done, then start implementing.
"""
    
    return prompt


async def run_agent_turn(
    client,
    messages: list,
    task: dict,
    progress: dict
) -> tuple[str, list]:
    """Run a single turn of the agent."""
    task_id = task.get("id", "local")
    
    console.print("\n[bold cyan]═══ Agent Turn ═══[/bold cyan]\n")
    await log_to_api(task_id, "INFO", "Starting agent turn")
    
    try:
        response = await call_llm(client, messages, TOOLS)
        
        assistant_content = []
        tool_calls = []
        text_response = ""
        
        for block in response.content:
            if block.type == "text":
                text_response += block.text
                assistant_content.append({"type": "text", "text": block.text})
                console.print(Panel(Markdown(block.text), title="Agent", border_style="green"))
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
                console.print(f"[dim]   Executing {tool_call.name}...[/dim]")
                result = await execute_tool(tool_call.name, tool_call.input)
                
                display_result = result[:500] + "..." if len(result) > 500 else result
                console.print(f"[dim]   → {display_result}[/dim]")
                
                # Check if this was a screenshot
                if tool_call.name == "browser_screenshot" and "Screenshot saved" in result:
                    filename = result.split(": ")[-1].strip()
                    await register_screenshot(task_id, filename)
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result
                })
            
            messages.append({"role": "user", "content": tool_results})
            return "continue", messages
        
        if response.stop_reason == "end_turn":
            completion_signals = [
                "task complete",
                "task is complete", 
                "successfully completed",
                "all done",
                "finished implementing"
            ]
            
            if any(signal in text_response.lower() for signal in completion_signals):
                await update_task_status(task_id, "COMPLETED", 100)
                return "complete", messages
        
        return "continue", messages
        
    except Exception as e:
        console.print(f"[red]Error during agent turn: {e}[/red]")
        await log_to_api(task_id, "ERROR", str(e))
        return "error", messages


async def run_autonomous_agent():
    """Main agent loop."""
    console.print(Panel.fit(
        "[bold magenta]🤖 Docker Autonomous Agent[/bold magenta]\n"
        f"Mode: {'Headless' if AGENT_HEADLESS else 'GUI (VNC)'}\n"
        "Fully autonomous coding - no permissions required",
        border_style="magenta"
    ))
    
    task = load_task()
    progress = load_progress()
    task_id = task.get("id", "local")
    
    console.print(f"\n[bold]Task:[/bold] {task.get('name', 'Unknown')}")
    console.print(f"[bold]Workspace:[/bold] {WORKSPACE}")
    console.print(f"[bold]Max Iterations:[/bold] {MAX_ITERATIONS}")
    console.print(f"[bold]API URL:[/bold] {API_URL}")
    
    # Update task status
    await update_task_status(task_id, "RUNNING", 0)
    await log_to_api(task_id, "INFO", f"Agent started - Mode: {'Headless' if AGENT_HEADLESS else 'GUI'}")
    
    client = create_client()
    task_prompt = format_task_prompt(task, progress)
    
    messages = [
        {"role": "user", "content": task_prompt}
    ]
    
    iteration = progress.get("iteration", 0)
    
    while iteration < MAX_ITERATIONS:
        iteration += 1
        progress["iteration"] = iteration
        
        # Update progress percentage
        progress_pct = min(int((iteration / MAX_ITERATIONS) * 100), 99)
        await update_task_status(task_id, "RUNNING", progress_pct)
        
        console.print(f"\n[bold blue]━━━ Iteration {iteration}/{MAX_ITERATIONS} ━━━[/bold blue]")
        
        status, messages = await run_agent_turn(client, messages, task, progress)
        
        save_progress(progress)
        
        if status == "complete":
            console.print("\n[bold green]✓ Task completed successfully![/bold green]")
            progress["current_phase"] = "completed"
            save_progress(progress)
            await log_to_api(task_id, "INFO", "Task completed successfully!")
            break
        elif status == "error":
            console.print("\n[yellow]⚠ Error occurred, will retry...[/yellow]")
            await asyncio.sleep(AUTO_CONTINUE_DELAY)
            continue
        
        if iteration < MAX_ITERATIONS:
            console.print(f"\n[dim]Continuing in {AUTO_CONTINUE_DELAY}s...[/dim]")
            await asyncio.sleep(AUTO_CONTINUE_DELAY)
    
    if iteration >= MAX_ITERATIONS:
        console.print(f"\n[yellow]Reached max iterations ({MAX_ITERATIONS})[/yellow]")
        progress["notes"].append(f"Stopped at iteration {iteration}")
        save_progress(progress)
        await update_task_status(task_id, "PAUSED", progress_pct)
    
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
