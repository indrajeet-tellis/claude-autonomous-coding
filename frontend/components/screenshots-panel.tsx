'use client'

import { useState } from 'react'
import { useScreenshots, useTasks } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Loader2, X } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function ScreenshotsPanel() {
    const { data: tasks } = useTasks()
    const activeTask = tasks?.find((t) => t.status === 'RUNNING') || tasks?.[0]
    const { data: screenshots, isLoading } = useScreenshots(activeTask?.id || '')

    const [selectedImage, setSelectedImage] = useState<string | null>(null)

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
            <div>
                <h2 className="text-2xl font-bold">Screenshots</h2>
                <p className="text-muted-foreground">
                    {activeTask ? `Screenshots from: ${activeTask.name}` : 'No active task'}
                </p>
            </div>

            {/* Screenshot Grid */}
            <ScrollArea className="h-[600px]">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {screenshots?.map((screenshot) => (
                        <Card
                            key={screenshot.id}
                            className="overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary transition-all"
                            onClick={() => setSelectedImage(`${API_URL}${screenshot.path}`)}
                        >
                            <CardContent className="p-0">
                                <div className="aspect-video bg-muted relative">
                                    <img
                                        src={`${API_URL}${screenshot.path}`}
                                        alt={screenshot.filename}
                                        className="w-full h-full object-cover"
                                        loading="lazy"
                                    />
                                </div>
                                <div className="p-2">
                                    <p className="text-xs font-mono truncate">{screenshot.filename}</p>
                                    <p className="text-xs text-muted-foreground">
                                        {formatDistanceToNow(new Date(screenshot.createdAt), { addSuffix: true })}
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    ))}

                    {screenshots?.length === 0 && (
                        <div className="col-span-full text-center py-12 text-muted-foreground">
                            No screenshots yet. The agent will capture screenshots during browser testing.
                        </div>
                    )}
                </div>
            </ScrollArea>

            {/* Lightbox */}
            {selectedImage && (
                <div
                    className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
                    onClick={() => setSelectedImage(null)}
                >
                    <button
                        className="absolute top-4 right-4 text-white hover:text-gray-300"
                        onClick={() => setSelectedImage(null)}
                    >
                        <X className="h-8 w-8" />
                    </button>
                    <img
                        src={selectedImage}
                        alt="Screenshot"
                        className="max-w-full max-h-full object-contain"
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
            )}
        </div>
    )
}
