'use client'

import { useState } from 'react'
import { useAgentStatus, useAgentControl } from '@/lib/api'
import { useUIStore } from '@/lib/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Eye, EyeOff, Save, Loader2 } from 'lucide-react'

export function SettingsPanel() {
    const { data: status } = useAgentStatus()
    const control = useAgentControl()
    const { vncUrl, setVncUrl, isHeadless, setHeadless } = useUIStore()

    const [localVncUrl, setLocalVncUrl] = useState(vncUrl)

    const handleSaveVncUrl = () => {
        setVncUrl(localVncUrl)
    }

    const toggleHeadless = () => {
        const newValue = !isHeadless
        setHeadless(newValue)
        control.mutate({ action: 'start', headless: newValue })
    }

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold">Settings</h2>
                <p className="text-muted-foreground">Configure the agent dashboard</p>
            </div>

            {/* Agent Mode */}
            <Card>
                <CardHeader>
                    <CardTitle>Agent Mode</CardTitle>
                    <CardDescription>
                        Choose between GUI mode (visible in VNC) or headless mode (faster)
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            {isHeadless ? (
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <EyeOff className="h-5 w-5" />
                                    <span>Headless Mode</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 text-green-500">
                                    <Eye className="h-5 w-5" />
                                    <span>GUI Mode</span>
                                </div>
                            )}
                        </div>
                        <Button onClick={toggleHeadless} disabled={control.isPending}>
                            {control.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                            Switch to {isHeadless ? 'GUI' : 'Headless'}
                        </Button>
                    </div>

                    <div className="text-sm text-muted-foreground">
                        {isHeadless ? (
                            <ul className="list-disc list-inside space-y-1">
                                <li>Chrome runs invisibly in background</li>
                                <li>Faster execution, lower resource usage</li>
                                <li>Screenshots saved for viewing in gallery</li>
                            </ul>
                        ) : (
                            <ul className="list-disc list-inside space-y-1">
                                <li>Chrome visible in VNC desktop</li>
                                <li>Watch agent interact with browser in real-time</li>
                                <li>Can manually intervene if needed</li>
                            </ul>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* VNC Settings */}
            <Card>
                <CardHeader>
                    <CardTitle>VNC Settings</CardTitle>
                    <CardDescription>Configure VNC connection</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="vnc-url">noVNC URL</Label>
                        <div className="flex gap-2">
                            <Input
                                id="vnc-url"
                                value={localVncUrl}
                                onChange={(e) => setLocalVncUrl(e.target.value)}
                                placeholder="http://localhost:6080/vnc.html"
                            />
                            <Button onClick={handleSaveVncUrl}>
                                <Save className="h-4 w-4 mr-2" />
                                Save
                            </Button>
                        </div>
                    </div>

                    <div className="text-sm text-muted-foreground">
                        <p>Default password: <code className="bg-muted px-1 rounded">agentpass</code></p>
                        <p>Resolution: 1920x1080</p>
                    </div>
                </CardContent>
            </Card>

            {/* API Settings */}
            <Card>
                <CardHeader>
                    <CardTitle>API Connection</CardTitle>
                    <CardDescription>Backend API status</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2">
                        <div className={`h-2 w-2 rounded-full ${status ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className="text-sm">
                            {status ? 'Connected to backend' : 'Disconnected'}
                        </span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                        API URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
                    </p>
                </CardContent>
            </Card>
        </div>
    )
}
