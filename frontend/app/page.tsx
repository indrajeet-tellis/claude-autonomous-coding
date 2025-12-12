'use client'

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { TasksPanel } from '@/components/tasks-panel'
import { LogsPanel } from '@/components/logs-panel'
import { ScreenshotsPanel } from '@/components/screenshots-panel'
import { VNCPanel } from '@/components/vnc-panel'
import { SettingsPanel } from '@/components/settings-panel'
import { AgentControls } from '@/components/agent-controls'
import {
    ListTodo,
    ScrollText,
    Image,
    Monitor,
    Settings,
    Bot
} from 'lucide-react'

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState('tasks')

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border bg-card">
                <div className="container flex h-16 items-center justify-between px-4">
                    <div className="flex items-center gap-3">
                        <Bot className="h-8 w-8 text-primary" />
                        <div>
                            <h1 className="text-xl font-bold">Agent Dashboard</h1>
                            <p className="text-xs text-muted-foreground">Autonomous Coding Agent</p>
                        </div>
                    </div>
                    <AgentControls />
                </div>
            </header>

            {/* Main Content */}
            <main className="container px-4 py-6">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                    <TabsList className="grid w-full grid-cols-5 lg:w-[600px]">
                        <TabsTrigger value="tasks" className="flex items-center gap-2">
                            <ListTodo className="h-4 w-4" />
                            <span className="hidden sm:inline">Tasks</span>
                        </TabsTrigger>
                        <TabsTrigger value="logs" className="flex items-center gap-2">
                            <ScrollText className="h-4 w-4" />
                            <span className="hidden sm:inline">Logs</span>
                        </TabsTrigger>
                        <TabsTrigger value="screenshots" className="flex items-center gap-2">
                            <Image className="h-4 w-4" />
                            <span className="hidden sm:inline">Screenshots</span>
                        </TabsTrigger>
                        <TabsTrigger value="vnc" className="flex items-center gap-2">
                            <Monitor className="h-4 w-4" />
                            <span className="hidden sm:inline">VNC</span>
                        </TabsTrigger>
                        <TabsTrigger value="settings" className="flex items-center gap-2">
                            <Settings className="h-4 w-4" />
                            <span className="hidden sm:inline">Settings</span>
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="tasks" className="space-y-4">
                        <TasksPanel />
                    </TabsContent>

                    <TabsContent value="logs" className="space-y-4">
                        <LogsPanel />
                    </TabsContent>

                    <TabsContent value="screenshots" className="space-y-4">
                        <ScreenshotsPanel />
                    </TabsContent>

                    <TabsContent value="vnc" className="space-y-4">
                        <VNCPanel />
                    </TabsContent>

                    <TabsContent value="settings" className="space-y-4">
                        <SettingsPanel />
                    </TabsContent>
                </Tabs>
            </main>
        </div>
    )
}
