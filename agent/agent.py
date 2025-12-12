#!/usr/bin/env python3
"""
Autonomous Coding Agent with Claude Agent SDK
==============================================

Uses ClaudeSDKClient for streaming output with detailed tool logging.
Integrates with the dashboard API for real-time logs and progress.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

import httpx
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Claude Agent SDK imports
try:
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        ClaudeSDKClient,
        AssistantMessage,
        UserMessage,
        SystemMessage,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
    )
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Warning: claude-agent-sdk not installed")

console = Console()

# Configuration
WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
API_URL = os.environ.get("API_URL", "http://backend:8000")
MAX_TURNS = int(os.environ.get("MAX_ITERATIONS", "500"))


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
                    "message": message[:4000],  # Allow longer messages
                    "tool": tool,
                },
                timeout=5.0
            )
    except Exception as e:
        console.print(f"[dim]Failed to send log: {e}[/dim]")


async def update_task_status(task_id: str, status: str, progress: int = None):
    """Update task status in dashboard."""
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
            "description": "No task.yaml found.",
            "workspace": str(WORKSPACE)
        }
    
    with open(task_file) as f:
        task = yaml.safe_load(f)
    
    if "id" not in task:
        task["id"] = "local"
    
    if "workspace" in task:
        task["workspace_path"] = Path(task["workspace"])
    else:
        task["workspace_path"] = WORKSPACE
    
    return task


def format_task_prompt(task: dict) -> str:
    """Format the task into a prompt."""
    prompt = f"""## Task: {task.get('name', 'Unnamed Task')}

{task.get('description', 'No description provided.')}
"""
    
    criteria = task.get('success_criteria', [])
    if criteria:
        prompt += "\n### Success Criteria\n"
        for i, c in enumerate(criteria, 1):
            prompt += f"{i}. {c}\n"
    
    prompt += f"\nWork in: {task.get('workspace_path', WORKSPACE)}"
    return prompt


# ============================================================================
# Message Processing with Detailed Logging
# ============================================================================

async def process_message(task_id: str, message, turn_count: int):
    """Process SDK message and log details to dashboard."""
    
    if isinstance(message, UserMessage):
        # User messages often contain tool results
        for block in message.content:
            if isinstance(block, TextBlock):
                await log_to_api(task_id, "INFO", f"User: {block.text}")
            elif isinstance(block, ToolResultBlock):
                # Log tool result with content
                result_preview = str(block.content)[:500] if block.content else "No output"
                await log_to_api(
                    task_id, "RESULT",
                    f"Tool Result:\n{result_preview}",
                    tool=None
                )
                console.print(f"[dim cyan]→ Result: {result_preview[:200]}...[/dim cyan]")
                
    elif isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                # Claude's text response - log full text
                console.print(Panel(Markdown(block.text[:1500]), title="Claude", border_style="green"))
                await log_to_api(task_id, "INFO", block.text)
                
            elif isinstance(block, ToolUseBlock):
                # Log tool use with FULL input details
                tool_name = block.name
                tool_input = getattr(block, 'input', {})
                tool_id = getattr(block, 'id', '')
                
                # Format detailed tool info
                input_str = json.dumps(tool_input, indent=2) if tool_input else "{}"
                
                console.print(f"\n[bold yellow]🔧 {tool_name}[/bold yellow]")
                console.print(f"[dim]{input_str[:500]}[/dim]")
                
                # Log to dashboard with full details
                log_message = f"{tool_name}\n\nInput:\n```json\n{input_str}\n```"
                await log_to_api(task_id, "TOOL", log_message, tool=tool_name)
                
    elif isinstance(message, SystemMessage):
        # System messages for context
        content = getattr(message, 'content', '')
        if content and isinstance(content, str):
            await log_to_api(task_id, "DEBUG", f"System: {content[:200]}")
            
    elif isinstance(message, ResultMessage):
        # Task completed
        console.print("[bold green]✓ Task completed![/bold green]")
        
        # Log cost info if available
        cost = getattr(message, 'total_cost_usd', None)
        if cost:
            await log_to_api(task_id, "INFO", f"Task completed. Cost: ${cost:.4f}")
        else:
            await log_to_api(task_id, "INFO", "Task completed successfully!")
            
        await update_task_status(task_id, "COMPLETED", 100)
        return True  # Signal completion
    
    return False


# ============================================================================
# Main Agent with ClaudeSDKClient (Streaming)
# ============================================================================

async def run_agent(task: dict):
    """Run the agent using ClaudeSDKClient for streaming."""
    if not SDK_AVAILABLE:
        console.print("[red]Claude Agent SDK not available![/red]")
        return
        
    task_id = task.get("id", "local")
    workspace = task.get("workspace_path", WORKSPACE)
    
    console.print(Panel.fit(
        "[bold cyan]🚀 Claude Agent SDK - Streaming Mode[/bold cyan]\n"
        f"Workspace: {workspace}\n"
        f"Max Turns: {MAX_TURNS}",
        border_style="cyan"
    ))
    
    # Configure SDK options
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash", "Glob", "Grep", "TodoRead", "TodoWrite"],
        permission_mode='acceptEdits',
        cwd=str(workspace),
        max_turns=MAX_TURNS,
    )
    
    prompt = format_task_prompt(task)
    
    await update_task_status(task_id, "RUNNING", 0)
    await log_to_api(task_id, "INFO", "Agent started with Claude Agent SDK")
    
    turn_count = 0
    completed = False
    
    try:
        async with ClaudeSDKClient(options=options) as client:
            console.print(f"\n[bold]Sending prompt:[/bold]\n{prompt[:500]}...")
            await client.query(prompt)
            
            # Process all messages from the streaming response
            async for message in client.receive_messages():
                turn_count += 1
                
                # Update progress
                progress_pct = min(int((turn_count / MAX_TURNS) * 100), 99)
                if turn_count % 5 == 0:  # Update every 5 messages
                    await update_task_status(task_id, "RUNNING", progress_pct)
                
                # Process and log the message
                completed = await process_message(task_id, message, turn_count)
                
                if completed:
                    break
                    
                if turn_count >= MAX_TURNS * 3:  # Safety limit
                    console.print(f"[yellow]Reached message limit[/yellow]")
                    await update_task_status(task_id, "PAUSED", 99)
                    break
                    
    except Exception as e:
        error_msg = f"Error during SDK execution: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        await log_to_api(task_id, "ERROR", error_msg)
        await update_task_status(task_id, "FAILED", 0)
        raise
    
    if not completed:
        await log_to_api(task_id, "INFO", f"Agent stopped after {turn_count} messages")


# ============================================================================
# Entry Point
# ============================================================================

async def main():
    """Main entry point."""
    console.print(Panel.fit(
        "[bold magenta]🤖 Autonomous Coding Agent[/bold magenta]\n"
        f"SDK Available: {SDK_AVAILABLE}",
        border_style="magenta"
    ))
    
    task = load_task()
    console.print(f"\n[bold]Task:[/bold] {task.get('name', 'Unknown')}")
    console.print(f"[bold]Workspace:[/bold] {task.get('workspace_path', WORKSPACE)}")
    
    await run_agent(task)
    console.print("\n[bold]Agent session ended.[/bold]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        raise
