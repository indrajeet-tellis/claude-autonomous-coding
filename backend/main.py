"""
FastAPI Backend for Agent Dashboard
====================================

REST API for task management, real-time logs, and agent control.
Using SQLAlchemy with async PostgreSQL.
"""

import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager
from enum import Enum as PyEnum

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
import httpx

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.future import select
import uuid


# ============================================================================
# Configuration
# ============================================================================
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://agent:agentpass@postgres:5432/agent_db")
# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "secret")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DESKTOP_HOST = os.environ.get("DESKTOP_HOST", "desktop")
WORKSPACE_PATH = Path("/workspace")
SCREENSHOTS_PATH = Path("/app/screenshots")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# Database Models
# ============================================================================
Base = declarative_base()


class TaskStatus(PyEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class LogLevel(PyEnum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    TOOL = "TOOL"


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    yaml = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    logs = relationship("Log", back_populates="task", cascade="all, delete-orphan")
    screenshots = relationship("Screenshot", back_populates="task", cascade="all, delete-orphan")


class Log(Base):
    __tablename__ = "logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    level = Column(Enum(LogLevel), nullable=False)
    message = Column(Text, nullable=False)
    tool = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("Task", back_populates="logs")


class Screenshot(Base):
    __tablename__ = "screenshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("Task", back_populates="screenshots")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, default="")
    path = Column(String, nullable=False)  # /workspace/{name}
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="project")


# Add project_id to Task model - done via relationship
Task.project_id = Column(String, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
Task.project = relationship("Project", back_populates="tasks")


# Database engine
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session


# ============================================================================
# Pydantic Models
# ============================================================================
class TaskCreate(BaseModel):
    name: str
    description: str
    yaml: str
    project_id: Optional[str] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    yaml: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    project_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    name: str
    description: str
    yaml: str
    status: str
    progress: int
    projectId: Optional[str] = None
    projectName: Optional[str] = None
    createdAt: str
    updatedAt: str
    

class LogCreate(BaseModel):
    taskId: str
    level: str
    message: str
    tool: Optional[str] = None


class LogResponse(BaseModel):
    id: str
    taskId: str
    level: str
    message: str
    tool: Optional[str]
    timestamp: str
    
    class Config:
        from_attributes = True


class ScreenshotResponse(BaseModel):
    id: str
    taskId: str
    filename: str
    path: str
    createdAt: str
    
    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    path: str
    createdAt: str
    taskCount: int = 0
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class AgentCommand(BaseModel):
    action: str
    headless: Optional[bool] = None


# Update TaskCreate to accept project_id
TaskCreate.model_fields['project_id'] = None


# ============================================================================
# App Lifespan
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create directories
    WORKSPACE_PATH.mkdir(exist_ok=True)
    SCREENSHOTS_PATH.mkdir(exist_ok=True)
    
    yield
    
    # Shutdown
    await engine.dispose()


# ============================================================================
# FastAPI App
# ============================================================================
app = FastAPI(
    title="Agent Dashboard API",
    description="API for managing autonomous coding agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (screenshots)
try:
    SCREENSHOTS_PATH.mkdir(exist_ok=True)
    app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_PATH)), name="screenshots")
except Exception:
    pass

# Security
security = HTTPBasic()


# ============================================================================
# Authentication
# ============================================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, API_SECRET_KEY, algorithm="HS256")


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ============================================================================
# Auth Endpoints
# ============================================================================
@app.post("/api/auth/login", response_model=Token)
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    verify_credentials(credentials)
    token = create_access_token({"sub": credentials.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/auth/me")
async def get_current_user(username: str = Depends(verify_credentials)):
    return {"username": username}


# ============================================================================
# Task Endpoints
# ============================================================================
@app.get("/api/tasks")
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    result = await db.execute(select(Task).order_by(Task.created_at.desc()))
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "yaml": t.yaml,
            "status": t.status.value,
            "progress": t.progress,
            "createdAt": t.created_at.isoformat(),
            "updatedAt": t.updated_at.isoformat()
        }
        for t in tasks
    ]


@app.post("/api/tasks")
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    # Determine workspace path
    project = None
    if task.project_id:
        result = await db.execute(select(Project).where(Project.id == task.project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    new_task = Task(
        name=task.name,
        description=task.description,
        yaml=task.yaml,
        project_id=task.project_id
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Determine workspace: use project workspace if assigned, otherwise task-specific
    if project:
        workspace_path = project.path  # e.g., /workspace/my-project
        task_workspace = WORKSPACE_PATH / Path(project.path).name
    else:
        workspace_path = f"/workspace/{new_task.id}"
        task_workspace = WORKSPACE_PATH / new_task.id
    
    # Create workspace directory
    task_workspace.mkdir(parents=True, exist_ok=True)
    
    # Write task.yaml with workspace path
    task_file = task_workspace / "task.yaml"
    yaml_with_id = f"id: {new_task.id}\nworkspace: {workspace_path}\n{task.yaml}"
    task_file.write_text(yaml_with_id)
    
    # Also write to root workspace for backward compatibility
    root_task_file = WORKSPACE_PATH / "task.yaml"
    root_task_file.write_text(yaml_with_id)
    
    return {
        "id": new_task.id,
        "name": new_task.name,
        "description": new_task.description,
        "status": new_task.status.value,
        "workspace": workspace_path,
        "projectId": task.project_id,
        "projectName": project.name if project else None,
    }


@app.get("/api/tasks/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "yaml": task.yaml,
        "status": task.status.value,
        "progress": task.progress,
        "createdAt": task.created_at.isoformat(),
        "updatedAt": task.updated_at.isoformat()
    }


@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_update.name is not None:
        task.name = task_update.name
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.yaml is not None:
        task.yaml = task_update.yaml
        task_file = WORKSPACE_PATH / "task.yaml"
        task_file.write_text(task_update.yaml)
    if task_update.status is not None:
        task.status = TaskStatus(task_update.status)
    if task_update.progress is not None:
        task.progress = task_update.progress
    
    await db.commit()
    
    return {"message": "Task updated"}


@app.delete("/api/tasks/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    
    return {"message": "Task deleted"}


# ============================================================================
# Log Endpoints
# ============================================================================
@app.get("/api/tasks/{task_id}/logs")
async def get_logs(
    task_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    result = await db.execute(
        select(Log)
        .where(Log.task_id == task_id)
        .order_by(Log.timestamp.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "taskId": log.task_id,
            "level": log.level.value,
            "message": log.message,
            "tool": log.tool,
            "timestamp": log.timestamp.isoformat()
        }
        for log in logs
    ]


@app.post("/api/logs")
async def create_log(
    log: LogCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a log entry (called by agent, no auth required internally)"""
    new_log = Log(
        task_id=log.taskId,
        level=LogLevel(log.level),
        message=log.message,
        tool=log.tool,
    )
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    
    # Broadcast to WebSocket clients
    await broadcast_log({
        "id": new_log.id,
        "taskId": new_log.task_id,
        "level": new_log.level.value,
        "message": new_log.message,
        "tool": new_log.tool,
        "timestamp": new_log.timestamp.isoformat()
    })
    
    return {"id": new_log.id}


# ============================================================================
# Internal Task Status Update (no auth - for agent use only)
# ============================================================================
class TaskStatusUpdate(BaseModel):
    status: str
    progress: Optional[int] = None


@app.patch("/api/tasks/{task_id}/status")
async def update_task_status_internal(
    task_id: str,
    update: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update task status (called by agent, no auth required internally)"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = TaskStatus(update.status)
    if update.progress is not None:
        task.progress = update.progress
    
    await db.commit()
    
    return {"message": "Task status updated", "status": update.status}


# ============================================================================
# Screenshot Endpoints
# ============================================================================
@app.get("/api/tasks/{task_id}/screenshots")
async def get_screenshots(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    result = await db.execute(
        select(Screenshot)
        .where(Screenshot.task_id == task_id)
        .order_by(Screenshot.created_at.desc())
    )
    screenshots = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "taskId": s.task_id,
            "filename": s.filename,
            "path": s.path,
            "createdAt": s.created_at.isoformat()
        }
        for s in screenshots
    ]


@app.post("/api/screenshots")
async def create_screenshot(
    task_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    """Register a screenshot (called by agent)"""
    screenshot = Screenshot(
        task_id=task_id,
        filename=filename,
        path=f"/screenshots/{filename}",
    )
    db.add(screenshot)
    await db.commit()
    
    return {"id": screenshot.id}


# ============================================================================
# Project Endpoints
# ============================================================================
@app.get("/api/projects")
async def list_projects(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """List all projects with task counts"""
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    
    project_list = []
    for p in projects:
        # Count tasks in this project
        task_count_result = await db.execute(
            select(Task).where(Task.project_id == p.id)
        )
        task_count = len(task_count_result.scalars().all())
        
        project_list.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "path": p.path,
            "createdAt": p.created_at.isoformat(),
            "taskCount": task_count
        })
    
    return project_list


@app.post("/api/projects")
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """Create a new project (creates directory in workspace)"""
    import re
    
    # Sanitize project name for use as folder name
    folder_name = re.sub(r'[^a-zA-Z0-9_-]', '-', project.name.lower())
    folder_name = re.sub(r'-+', '-', folder_name).strip('-')
    
    project_path = WORKSPACE_PATH / folder_name
    
    # Check if folder already exists
    if project_path.exists():
        raise HTTPException(status_code=400, detail=f"Project folder '{folder_name}' already exists")
    
    # Create the directory
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Create project in database
    new_project = Project(
        name=project.name,
        description=project.description,
        path=f"/workspace/{folder_name}"
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    return {
        "id": new_project.id,
        "name": new_project.name,
        "description": new_project.description,
        "path": new_project.path,
        "createdAt": new_project.created_at.isoformat(),
        "taskCount": 0
    }


@app.get("/api/projects/{project_id}")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """Get a project with its files"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # List files in project directory
    project_path = WORKSPACE_PATH / Path(project.path).name
    files = []
    if project_path.exists():
        for item in project_path.iterdir():
            files.append({
                "name": item.name,
                "isDirectory": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0
            })
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "path": project.path,
        "createdAt": project.created_at.isoformat(),
        "files": files
    }


@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """Delete a project (keeps files, just removes from database)"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Remove project from database (tasks will have project_id set to NULL)
    await db.delete(project)
    await db.commit()
    
    return {"status": "deleted", "id": project_id}


# ============================================================================
# Agent Control Endpoints

# ============================================================================
@app.post("/api/agent/control")
async def control_agent(
    command: AgentCommand,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """Control the agent process via supervisor in desktop container"""
    action = command.action.lower()
    
    try:
        # Call desktop container's supervisor via HTTP
        # supervisord exposes XML-RPC at port 9001 when configured
        # For now, we'll use a simpler approach: call the agent script directly
        
        if action == "start":
            # Start the agent in background via HTTP call to a control endpoint
            # Since desktop container doesn't have a control API, we'll signal via file
            control_file = WORKSPACE_PATH / ".agent_control"
            control_file.write_text("start")
            
            return {
                "status": "ok", 
                "action": "start", 
                "message": "Agent start signal sent. The agent will pick up tasks from task.yaml."
            }
        elif action == "stop":
            control_file = WORKSPACE_PATH / ".agent_control"
            control_file.write_text("stop")
            
            # Reset all RUNNING tasks to PENDING
            result = await db.execute(
                select(Task).where(Task.status == TaskStatus.RUNNING)
            )
            running_tasks = result.scalars().all()
            for task in running_tasks:
                task.status = TaskStatus.PENDING
                task.progress = 0
            await db.commit()
            
            return {
                "status": "ok", 
                "action": "stop", 
                "message": f"Agent stop signal sent. Reset {len(running_tasks)} running task(s) to PENDING."
            }
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/tasks/{task_id}/run")
async def run_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """Run a specific task by updating task.yaml and starting the agent"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create/update workspace for this task
    task_workspace = WORKSPACE_PATH / task_id
    task_workspace.mkdir(parents=True, exist_ok=True)
    
    # Write task.yaml with workspace path
    task_file = task_workspace / "task.yaml"
    yaml_with_id = f"id: {task.id}\nworkspace: /workspace/{task.id}\n{task.yaml}"
    task_file.write_text(yaml_with_id)
    
    # Also write to root workspace (agent reads from here)
    root_task_file = WORKSPACE_PATH / "task.yaml"
    root_task_file.write_text(yaml_with_id)
    
    # Update task status to RUNNING
    task.status = TaskStatus.RUNNING
    task.progress = 0
    await db.commit()
    
    # Signal agent to start
    control_file = WORKSPACE_PATH / ".agent_control"
    control_file.write_text("start")
    
    return {
        "status": "ok",
        "message": f"Task '{task.name}' started",
        "task_id": task_id,
        "workspace": f"/workspace/{task_id}"
    }


@app.get("/api/agent/status")
async def get_agent_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """Get current agent status"""
    result = await db.execute(
        select(Task).where(Task.status == TaskStatus.RUNNING)
    )
    running_task = result.scalar_one_or_none()
    
    return {
        "running": running_task is not None,
        "currentTaskId": running_task.id if running_task else None,
        "headless": os.environ.get("AGENT_HEADLESS", "false") == "true"
    }


# ============================================================================
# WebSocket for Real-time Updates
# ============================================================================
connected_clients: List[WebSocket] = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


async def broadcast_log(log_data: dict):
    """Broadcast log to all connected WebSocket clients"""
    message = {"type": "log", "data": log_data}
    
    for client in list(connected_clients):
        try:
            await client.send_json(message)
        except Exception:
            if client in connected_clients:
                connected_clients.remove(client)


# ============================================================================
# Health Check
# ============================================================================
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
