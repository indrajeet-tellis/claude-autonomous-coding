'use client'

import { useState } from 'react'
import { useTasks, useCreateTask, useDeleteTask, useRunTask, useAgentControl, useProjects } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Plus, Trash2, Play, Square, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'


const defaultTaskYaml = `name: "My Task"

description: |
  Describe what you want the agent to build.
  Be specific about features and requirements.

success_criteria:
  - "Criterion 1"
  - "Criterion 2"

preferences:
  language: "python"
`

export function TasksPanel() {
    const { data: tasks, isLoading } = useTasks()
    const { data: projects } = useProjects()
    const createTask = useCreateTask()
    const deleteTask = useDeleteTask()
    const runTask = useRunTask()
    const agentControl = useAgentControl()

    const [isCreating, setIsCreating] = useState(false)
    const [newTask, setNewTask] = useState({
        name: '',
        description: '',
        yaml: defaultTaskYaml,
        project_id: '',
    })

    const handleCreate = async () => {
        await createTask.mutateAsync({
            ...newTask,
            project_id: newTask.project_id || undefined
        })
        setNewTask({ name: '', description: '', yaml: defaultTaskYaml, project_id: '' })
        setIsCreating(false)
    }

    const handleRunTask = async (taskId: string) => {
        await runTask.mutateAsync(taskId)
    }

    const handleStopAgent = async () => {
        await agentControl.mutateAsync({ action: 'stop' })
    }

    const isAnyTaskRunning = tasks?.some(t => t.status === 'RUNNING')

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'RUNNING':
                return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
            case 'COMPLETED':
                return <CheckCircle className="h-4 w-4 text-green-500" />
            case 'FAILED':
                return <XCircle className="h-4 w-4 text-red-500" />
            default:
                return <Clock className="h-4 w-4 text-gray-500" />
        }
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold">Tasks</h2>
                    <p className="text-muted-foreground">Create and manage agent tasks</p>
                </div>
                <div className="flex gap-2">
                    {isAnyTaskRunning && (
                        <Button
                            variant="destructive"
                            onClick={handleStopAgent}
                            disabled={agentControl.isPending}
                        >
                            {agentControl.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : (
                                <Square className="h-4 w-4 mr-2" />
                            )}
                            Stop Agent
                        </Button>
                    )}
                    <Button onClick={() => setIsCreating(true)} disabled={isCreating}>
                        <Plus className="h-4 w-4 mr-2" />
                        New Task
                    </Button>
                </div>
            </div>

            {/* Create Task Form */}
            {isCreating && (
                <Card>
                    <CardHeader>
                        <CardTitle>Create New Task</CardTitle>
                        <CardDescription>Define what the agent should build</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Task Name</Label>
                                <Input
                                    id="name"
                                    value={newTask.name}
                                    onChange={(e) => setNewTask({ ...newTask, name: e.target.value })}
                                    placeholder="e.g., Todo App"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="project">Project (Optional)</Label>
                                <select
                                    id="project"
                                    value={newTask.project_id}
                                    onChange={(e) => setNewTask({ ...newTask, project_id: e.target.value })}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                >
                                    <option value="">No Project (isolated workspace)</option>
                                    {projects?.map((p) => (
                                        <option key={p.id} value={p.id}>
                                            📁 {p.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Input
                                id="description"
                                value={newTask.description}
                                onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                                placeholder="Brief description"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="yaml">Task YAML</Label>
                            <textarea
                                id="yaml"
                                value={newTask.yaml}
                                onChange={(e) => setNewTask({ ...newTask, yaml: e.target.value })}
                                className="w-full h-64 p-3 font-mono text-sm bg-background border rounded-md"
                            />
                        </div>
                        <div className="flex gap-2">
                            <Button onClick={handleCreate} disabled={createTask.isPending}>
                                {createTask.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}

                                Create Task
                            </Button>
                            <Button variant="outline" onClick={() => setIsCreating(false)}>
                                Cancel
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Task List */}
            <ScrollArea className="h-[500px]">
                <div className="space-y-3">
                    {tasks?.map((task) => (
                        <Card key={task.id} className="hover:bg-accent/50 transition-colors">
                            <CardContent className="p-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-3 flex-1">
                                        {getStatusIcon(task.status)}
                                        <div className="flex-1">
                                            <h3 className="font-semibold">{task.name}</h3>
                                            <p className="text-sm text-muted-foreground">{task.description}</p>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                Created {formatDistanceToNow(new Date(task.createdAt), { addSuffix: true })}
                                            </p>

                                            {/* Progress Bar */}
                                            {task.status === 'RUNNING' && (
                                                <div className="mt-2">
                                                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                                                        <span>Progress</span>
                                                        <span>{task.progress || 0}%</span>
                                                    </div>
                                                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-blue-500 transition-all duration-500"
                                                            style={{ width: `${task.progress || 0}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={`text-xs px-2 py-1 rounded ${task.status === 'RUNNING' ? 'bg-blue-500/20 text-blue-500' :
                                            task.status === 'COMPLETED' ? 'bg-green-500/20 text-green-500' :
                                                task.status === 'FAILED' ? 'bg-red-500/20 text-red-500' :
                                                    'bg-gray-500/20 text-gray-500'
                                            }`}>
                                            {task.status}
                                        </span>
                                        {task.status !== 'RUNNING' && (
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => handleRunTask(task.id)}
                                                disabled={isAnyTaskRunning || runTask.isPending}
                                                title="Run this task"
                                            >
                                                <Play className="h-4 w-4 text-green-500" />
                                            </Button>
                                        )}
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => deleteTask.mutate(task.id)}
                                            disabled={task.status === 'RUNNING'}
                                        >
                                            <Trash2 className="h-4 w-4 text-destructive" />
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}

                    {tasks?.length === 0 && (
                        <div className="text-center py-12 text-muted-foreground">
                            No tasks yet. Create one to get started!
                        </div>
                    )}
                </div>
            </ScrollArea>
        </div>
    )
}
