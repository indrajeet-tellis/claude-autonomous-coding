'use client'

import { useEffect, useState } from 'react'
import { useLogs, connectWebSocket, useTasks } from '@/lib/api'
import { useAgentStore } from '@/lib/store'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, Trash2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export function LogsPanel() {
    const { data: tasks } = useTasks()
    const [selectedTaskId, setSelectedTaskId] = useState<string>('')

    // Auto-select first task or running task
    useEffect(() => {
        if (tasks && tasks.length > 0 && !selectedTaskId) {
            const runningTask = tasks.find((t) => t.status === 'RUNNING')
            setSelectedTaskId(runningTask?.id || tasks[0]?.id || '')
        }
    }, [tasks, selectedTaskId])

    const selectedTask = tasks?.find((t) => t.id === selectedTaskId)
    const { data: logs, isLoading } = useLogs(selectedTaskId)
    const { logs: realtimeLogs, addLog, clearLogs } = useAgentStore()

    // Connect WebSocket for real-time logs
    useEffect(() => {
        const ws = connectWebSocket((data) => {
            if (data.type === 'log') {
                addLog(data.data)
            }
        })

        return () => ws.close()
    }, [addLog])

    // Combine API logs with realtime logs (filter by selected task)
    const allLogs = [
        ...realtimeLogs.filter(log => log.taskId === selectedTaskId),
        ...(logs || [])
    ].slice(0, 500)

    const getLevelClass = (level: string) => {
        switch (level) {
            case 'INFO': return 'log-info'
            case 'WARN': return 'log-warn'
            case 'ERROR': return 'log-error'
            case 'DEBUG': return 'log-debug'
            case 'TOOL': return 'log-tool'
            default: return ''
        }
    }

    const getLevelBadge = (level: string) => {
        const colors: Record<string, string> = {
            INFO: 'bg-blue-500/20 text-blue-400',
            WARN: 'bg-yellow-500/20 text-yellow-400',
            ERROR: 'bg-red-500/20 text-red-400',
            DEBUG: 'bg-purple-500/20 text-purple-400',
            TOOL: 'bg-green-500/20 text-green-400',
        }
        return colors[level] || 'bg-gray-500/20 text-gray-400'
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'RUNNING': return 'bg-blue-500/20 text-blue-400'
            case 'COMPLETED': return 'bg-green-500/20 text-green-400'
            case 'FAILED': return 'bg-red-500/20 text-red-400'
            default: return 'bg-gray-500/20 text-gray-400'
        }
    }

    if (isLoading && !logs) {
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
                <div className="flex items-center gap-4">
                    <div>
                        <h2 className="text-2xl font-bold">Logs</h2>
                        <p className="text-muted-foreground">
                            {selectedTask ? `Viewing: ${selectedTask.name}` : 'Select a task'}
                        </p>
                    </div>

                    {/* Task Selector */}
                    <Select value={selectedTaskId} onValueChange={setSelectedTaskId}>
                        <SelectTrigger className="w-[250px]">
                            <SelectValue placeholder="Select a task..." />
                        </SelectTrigger>
                        <SelectContent>
                            {tasks?.map((task) => (
                                <SelectItem key={task.id} value={task.id}>
                                    <div className="flex items-center gap-2">
                                        <span className={`text-xs px-1.5 py-0.5 rounded ${getStatusBadge(task.status)}`}>
                                            {task.status}
                                        </span>
                                        <span className="truncate max-w-[150px]">{task.name}</span>
                                    </div>
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <Button variant="outline" size="sm" onClick={clearLogs}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Clear
                </Button>
            </div>

            {/* Log Viewer */}
            <Card className="bg-black/50">
                <CardContent className="p-0">
                    <ScrollArea className="h-[600px]">
                        <div className="font-mono text-sm p-4 space-y-1">
                            {allLogs.map((log, index) => (
                                <div key={log.id || index} className="flex items-start gap-2 hover:bg-white/5 px-2 py-1 rounded">
                                    <span className="text-muted-foreground text-xs shrink-0 w-16">
                                        {new Date(log.timestamp).toLocaleTimeString()}
                                    </span>
                                    <span className={`text-xs px-1.5 py-0.5 rounded shrink-0 w-12 text-center ${getLevelBadge(log.level)}`}>
                                        {log.level}
                                    </span>
                                    {log.tool && (
                                        <span className="text-xs px-1.5 py-0.5 rounded bg-accent text-accent-foreground shrink-0">
                                            {log.tool}
                                        </span>
                                    )}
                                    <span className={`${getLevelClass(log.level)} break-all`}>
                                        {log.message}
                                    </span>
                                </div>
                            ))}

                            {allLogs.length === 0 && (
                                <div className="text-center py-12 text-muted-foreground">
                                    {selectedTaskId
                                        ? 'No logs yet for this task. Start the agent to see output.'
                                        : 'Select a task to view logs.'
                                    }
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </CardContent>
            </Card>
        </div>
    )
}
