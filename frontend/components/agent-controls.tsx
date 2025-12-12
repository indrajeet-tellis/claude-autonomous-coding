'use client'

import { useAgentStatus, useAgentControl } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Play, Square, Eye, EyeOff, Loader2 } from 'lucide-react'

export function AgentControls() {
    const { data: status, isLoading } = useAgentStatus()
    const control = useAgentControl()

    const handleStart = () => {
        control.mutate({ action: 'start', headless: status?.headless })
    }

    const handleStop = () => {
        control.mutate({ action: 'stop' })
    }

    const toggleHeadless = () => {
        control.mutate({ action: 'start', headless: !status?.headless })
    }

    if (isLoading) {
        return (
            <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">Loading...</span>
            </div>
        )
    }

    return (
        <div className="flex items-center gap-4">
            {/* Status indicator */}
            <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${status?.running ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
                <span className="text-sm text-muted-foreground">
                    {status?.running ? 'Running' : 'Stopped'}
                </span>
            </div>

            {/* Headless toggle */}
            <Button
                variant="outline"
                size="sm"
                onClick={toggleHeadless}
                disabled={control.isPending}
                title={status?.headless ? 'Switch to GUI mode' : 'Switch to headless mode'}
            >
                {status?.headless ? (
                    <>
                        <EyeOff className="h-4 w-4 mr-1" />
                        Headless
                    </>
                ) : (
                    <>
                        <Eye className="h-4 w-4 mr-1" />
                        GUI
                    </>
                )}
            </Button>

            {/* Start/Stop */}
            {status?.running ? (
                <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleStop}
                    disabled={control.isPending}
                >
                    {control.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                        <Square className="h-4 w-4 mr-1" />
                    )}
                    Stop
                </Button>
            ) : (
                <Button
                    variant="default"
                    size="sm"
                    onClick={handleStart}
                    disabled={control.isPending}
                >
                    {control.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                        <Play className="h-4 w-4 mr-1" />
                    )}
                    Start
                </Button>
            )}
        </div>
    )
}
