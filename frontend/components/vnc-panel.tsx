'use client'

import { useUIStore } from '@/lib/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ExternalLink, Maximize2, RefreshCw } from 'lucide-react'
import { useState } from 'react'

export function VNCPanel() {
    const { vncUrl } = useUIStore()
    const [key, setKey] = useState(0)

    const handleRefresh = () => {
        setKey((k) => k + 1)
    }

    const handleOpenExternal = () => {
        window.open(vncUrl, '_blank')
    }

    const handleFullscreen = () => {
        const iframe = document.getElementById('vnc-frame') as HTMLIFrameElement
        if (iframe) {
            iframe.requestFullscreen()
        }
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold">VNC Desktop</h2>
                    <p className="text-muted-foreground">Watch the agent work in real-time</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={handleRefresh}>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Refresh
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleFullscreen}>
                        <Maximize2 className="h-4 w-4 mr-2" />
                        Fullscreen
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleOpenExternal}>
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Open in Tab
                    </Button>
                </div>
            </div>

            {/* VNC iframe */}
            <Card className="overflow-hidden">
                <CardContent className="p-0">
                    <div className="aspect-video bg-black">
                        <iframe
                            id="vnc-frame"
                            key={key}
                            src={vncUrl}
                            className="w-full h-full border-0"
                            allow="fullscreen"
                            title="VNC Desktop"
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Instructions */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">VNC Controls</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground space-y-2">
                    <p>• Click inside the VNC window to interact with the desktop</p>
                    <p>• Use keyboard and mouse as normal</p>
                    <p>• The agent controls the desktop automatically when running</p>
                    <p>• You can take over control anytime by clicking and typing</p>
                    <p>• VNC password: <code className="bg-muted px-1 rounded">agentpass</code></p>
                </CardContent>
            </Card>
        </div>
    )
}
