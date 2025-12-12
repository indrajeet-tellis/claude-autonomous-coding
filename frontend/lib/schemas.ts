import { z } from 'zod'

// Task schema
export const taskSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    description: z.string().min(1, 'Description is required'),
    yaml: z.string().min(1, 'Task YAML is required'),
    project_id: z.string().optional(),
})

export type TaskFormData = z.infer<typeof taskSchema>

// Task API response
export const taskResponseSchema = z.object({
    id: z.string(),
    name: z.string(),
    description: z.string(),
    yaml: z.string(),
    status: z.enum(['PENDING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED']),
    progress: z.number(),
    projectId: z.string().nullable().optional(),
    projectName: z.string().nullable().optional(),
    createdAt: z.string(),
    updatedAt: z.string(),
})

export type Task = z.infer<typeof taskResponseSchema>


// Log schema
export const logSchema = z.object({
    id: z.string(),
    taskId: z.string(),
    level: z.enum(['INFO', 'WARN', 'ERROR', 'DEBUG', 'TOOL']),
    message: z.string(),
    tool: z.string().nullable(),
    timestamp: z.string(),
})

export type Log = z.infer<typeof logSchema>

// Screenshot schema
export const screenshotSchema = z.object({
    id: z.string(),
    taskId: z.string(),
    filename: z.string(),
    path: z.string(),
    createdAt: z.string(),
})

export type Screenshot = z.infer<typeof screenshotSchema>

// Agent status
export const agentStatusSchema = z.object({
    running: z.boolean(),
    currentTaskId: z.string().nullable(),
    headless: z.boolean(),
})

export type AgentStatus = z.infer<typeof agentStatusSchema>
