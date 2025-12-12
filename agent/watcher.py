#!/usr/bin/env python3
"""
Agent Control Watcher
=====================

Monitors /workspace/.agent_control for signals and starts/stops the agent accordingly.
Runs as a supervisor process.
"""

import subprocess
import time
import os
from pathlib import Path

WORKSPACE = Path("/workspace")
CONTROL_FILE = WORKSPACE / ".agent_control"
AGENT_SCRIPT = Path("/app/agent/agent.py")
PID_FILE = Path("/tmp/agent.pid")

current_process = None


def get_task_workspace():
    """Read workspace path from task.yaml if available."""
    task_file = WORKSPACE / "task.yaml"
    if task_file.exists():
        try:
            import yaml
            with open(task_file) as f:
                task = yaml.safe_load(f)
                if task and "workspace" in task:
                    return task["workspace"]
        except:
            pass
    return str(WORKSPACE)


def start_agent():
    global current_process
    
    if current_process and current_process.poll() is None:
        print("Agent is already running")
        return
    
    # Get task-specific workspace
    task_workspace = get_task_workspace()
    print(f"Starting agent with workspace: {task_workspace}")
    
    # Set environment with task-specific workspace
    env = os.environ.copy()
    env["WORKSPACE"] = task_workspace
    
    current_process = subprocess.Popen(
        ["python3", str(AGENT_SCRIPT)],
        cwd=task_workspace,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # Store PID
    PID_FILE.write_text(str(current_process.pid))
    print(f"Agent started with PID {current_process.pid}")


def stop_agent():
    global current_process
    
    print("Stop agent requested...")
    
    # Try to stop via current_process reference
    if current_process and current_process.poll() is None:
        print(f"Stopping agent process {current_process.pid}...")
        current_process.terminate()
        try:
            current_process.wait(timeout=10)
        except:
            current_process.kill()
        current_process = None
        print("Agent stopped via process reference")
    
    # Also try to kill via PID file (backup method)
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            print(f"Killing agent via PID file: {pid}")
            os.kill(pid, 9)  # SIGKILL
        except (ValueError, ProcessLookupError) as e:
            print(f"Could not kill via PID: {e}")
        finally:
            PID_FILE.unlink()
    
    # Also try to find and kill any python agent.py process
    try:
        import subprocess
        result = subprocess.run(['pkill', '-f', 'agent.py'], capture_output=True)
        if result.returncode == 0:
            print("Killed agent.py via pkill")
    except Exception as e:
        print(f"pkill failed: {e}")
    
    current_process = None
    print("Stop agent completed")


def main():
    global current_process
    
    print("Agent control watcher started")
    print(f"Monitoring: {CONTROL_FILE}")
    
    # Cleanup old control file
    if CONTROL_FILE.exists():
        CONTROL_FILE.unlink()
    
    last_mtime = 0
    
    while True:
        try:
            if CONTROL_FILE.exists():
                mtime = CONTROL_FILE.stat().st_mtime
                
                if mtime > last_mtime:
                    last_mtime = mtime
                    command = CONTROL_FILE.read_text().strip().lower()
                    print(f"Received command: {command}")
                    
                    if command == "start":
                        start_agent()
                    elif command == "stop":
                        stop_agent()
                    
                    # Remove control file after processing
                    CONTROL_FILE.unlink()
            
            # Check if agent process crashed
            if current_process and current_process.poll() is not None:
                exit_code = current_process.returncode
                print(f"Agent process exited with code {exit_code}")
                current_process = None
                if PID_FILE.exists():
                    PID_FILE.unlink()
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
