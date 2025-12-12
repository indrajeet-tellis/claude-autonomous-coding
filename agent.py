#!/usr/bin/env python3
"""
Autonomous Coding Agent
=======================

A fully autonomous coding agent that runs in Docker and requires no user intervention.
Handles any task type: web apps, APIs, scripts, CLI tools, etc.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from client import create_client, call_llm
from tools import TOOLS, execute_tool
from prompts import get_system_prompt

console = Console()

# Configuration
WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "100"))
AUTO_CONTINUE_DELAY = int(os.environ.get("AUTO_CONTINUE_DELAY", "3"))


def load_task() -> dict:
    """Load task definition from workspace."""
    task_file = WORKSPACE / "task.yaml"
    
    if not task_file.exists():
        # Create a default task if none exists
        default_task = {
            "name": "Interactive Mode",
            "description": "No task.yaml found. Running in interactive mode - waiting for instructions.",
            "success_criteria": [],
            "preferences": {}
        }
        return default_task
    
    with open(task_file) as f:
        return yaml.safe_load(f)


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
    
    # Add progress context
    if progress.get('notes'):
        prompt += "\n**Previous Session Notes:**\n"
        for note in progress['notes'][-5:]:  # Last 5 notes
            prompt += f"- {note}\n"
    
    prompt += f"\n**Current Phase:** {progress.get('current_phase', 'starting')}"
    prompt += f"\n**Iteration:** {progress.get('iteration', 0) + 1}"
    
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
    progress: dict
) -> tuple[str, list]:
    """
    Run a single turn of the agent.
    
    Returns:
        (status, updated_messages)
        status is one of: "continue", "complete", "error"
    """
    console.print("\n[bold cyan]═══ Agent Turn ═══[/bold cyan]\n")
    
    try:
        # Call LLM with tools
        response = await call_llm(client, messages, TOOLS)
        
        # Process response
        assistant_content = []
        tool_calls = []
        text_response = ""
        
        for block in response.content:
            if block.type == "text":
                text_response += block.text
                assistant_content.append({"type": "text", "text": block.text})
                console.print(Panel(Markdown(block.text), title="Agent", border_style="green"))
            elif block.type == "tool_use":
                tool_calls.append(block)
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                console.print(f"[yellow]🔧 Tool: {block.name}[/yellow]")
        
        # Add assistant message
        messages.append({"role": "assistant", "content": assistant_content})
        
        # Execute tool calls if any
        if tool_calls:
            tool_results = []
            for tool_call in tool_calls:
                console.print(f"[dim]   Executing {tool_call.name}...[/dim]")
                result = await execute_tool(tool_call.name, tool_call.input)
                
                # Truncate long results for display
                display_result = result[:500] + "..." if len(result) > 500 else result
                console.print(f"[dim]   → {display_result}[/dim]")
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result
                })
            
            # Add tool results
            messages.append({"role": "user", "content": tool_results})
            
            # Continue the conversation
            return "continue", messages
        
        # No tool calls - check if we're done
        if response.stop_reason == "end_turn":
            # Check for completion signals in the text
            completion_signals = [
                "task complete",
                "task is complete", 
                "successfully completed",
                "all done",
                "finished implementing"
            ]
            
            if any(signal in text_response.lower() for signal in completion_signals):
                return "complete", messages
        
        return "continue", messages
        
    except Exception as e:
        console.print(f"[red]Error during agent turn: {e}[/red]")
        return "error", messages


async def run_autonomous_agent():
    """Main agent loop."""
    console.print(Panel.fit(
        "[bold magenta]🤖 Docker Autonomous Agent[/bold magenta]\n"
        "Fully autonomous coding - no permissions required",
        border_style="magenta"
    ))
    
    # Load task and progress
    task = load_task()
    progress = load_progress()
    
    console.print(f"\n[bold]Task:[/bold] {task.get('name', 'Unknown')}")
    console.print(f"[bold]Workspace:[/bold] {WORKSPACE}")
    console.print(f"[bold]Max Iterations:[/bold] {MAX_ITERATIONS}")
    
    # Initialize client
    client = create_client()
    
    # Build initial messages
    system_prompt = get_system_prompt()
    task_prompt = format_task_prompt(task, progress)
    
    messages = [
        {"role": "user", "content": task_prompt}
    ]
    
    # Main loop
    iteration = progress.get("iteration", 0)
    
    while iteration < MAX_ITERATIONS:
        iteration += 1
        progress["iteration"] = iteration
        
        console.print(f"\n[bold blue]━━━ Iteration {iteration}/{MAX_ITERATIONS} ━━━[/bold blue]")
        
        # Run agent turn
        status, messages = await run_agent_turn(client, messages, progress)
        
        # Save progress after each turn
        save_progress(progress)
        
        if status == "complete":
            console.print("\n[bold green]✓ Task completed successfully![/bold green]")
            progress["current_phase"] = "completed"
            save_progress(progress)
            break
        elif status == "error":
            console.print("\n[yellow]⚠ Error occurred, will retry...[/yellow]")
            await asyncio.sleep(AUTO_CONTINUE_DELAY)
            continue
        
        # Auto-continue delay
        if iteration < MAX_ITERATIONS:
            console.print(f"\n[dim]Continuing in {AUTO_CONTINUE_DELAY}s...[/dim]")
            await asyncio.sleep(AUTO_CONTINUE_DELAY)
    
    if iteration >= MAX_ITERATIONS:
        console.print(f"\n[yellow]Reached max iterations ({MAX_ITERATIONS})[/yellow]")
        progress["notes"].append(f"Stopped at iteration {iteration}")
        save_progress(progress)
    
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
