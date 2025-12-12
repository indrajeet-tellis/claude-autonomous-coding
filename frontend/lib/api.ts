import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Task, TaskFormData, Log, Screenshot, AgentStatus } from './schemas'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Get auth header from localStorage
function getAuthHeader(): HeadersInit {
    const credentials = localStorage.getItem('auth')
    if (credentials) {
        return { 'Authorization': `Basic ${credentials}` }
    }
    return {}
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...getAuthHeader(),
            ...options.headers,
        },
    })

    if (!response.ok) {
        if (response.status === 401) {
            localStorage.removeItem('auth')
            window.location.href = '/login'
        }
        throw new Error(`API error: ${response.status}`)
    }

    return response.json()
}

// Tasks
export function useTasks() {
    return useQuery<Task[]>({
        queryKey: ['tasks'],
        queryFn: () => fetchWithAuth(`${API_URL}/api/tasks`),
    })
}

export function useTask(id: string) {
    return useQuery<Task>({
        queryKey: ['tasks', id],
        queryFn: () => fetchWithAuth(`${API_URL}/api/tasks/${id}`),
        enabled: !!id,
    })
}

export function useCreateTask() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (data: TaskFormData) =>
            fetchWithAuth(`${API_URL}/api/tasks`, {
                method: 'POST',
                body: JSON.stringify(data),
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] })
        },
    })
}

export function useUpdateTask() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<TaskFormData> }) =>
            fetchWithAuth(`${API_URL}/api/tasks/${id}`, {
                method: 'PATCH',
                body: JSON.stringify(data),
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] })
        },
    })
}

export function useDeleteTask() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (id: string) =>
            fetchWithAuth(`${API_URL}/api/tasks/${id}`, {
                method: 'DELETE',
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] })
        },
    })
}

// Logs
export function useLogs(taskId: string) {
    return useQuery<Log[]>({
        queryKey: ['logs', taskId],
        queryFn: () => fetchWithAuth(`${API_URL}/api/tasks/${taskId}/logs`),
        enabled: !!taskId,
        refetchInterval: 2000, // Poll every 2 seconds
    })
}

// Screenshots
export function useScreenshots(taskId: string) {
    return useQuery<Screenshot[]>({
        queryKey: ['screenshots', taskId],
        queryFn: () => fetchWithAuth(`${API_URL}/api/tasks/${taskId}/screenshots`),
        enabled: !!taskId,
        refetchInterval: 5000,
    })
}

// Agent control
export function useAgentStatus() {
    return useQuery<AgentStatus>({
        queryKey: ['agent-status'],
        queryFn: () => fetchWithAuth(`${API_URL}/api/agent/status`),
        refetchInterval: 3000,
    })
}

export function useAgentControl() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (command: { action: string; headless?: boolean }) =>
            fetchWithAuth(`${API_URL}/api/agent/control`, {
                method: 'POST',
                body: JSON.stringify(command),
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['agent-status'] })
            queryClient.invalidateQueries({ queryKey: ['tasks'] })
        },
    })
}

export function useRunTask() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (taskId: string) =>
            fetchWithAuth(`${API_URL}/api/tasks/${taskId}/run`, {
                method: 'POST',
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['agent-status'] })
            queryClient.invalidateQueries({ queryKey: ['tasks'] })
        },
    })
}


// Projects
export function useProjects() {
    return useQuery<any[]>({
        queryKey: ['projects'],
        queryFn: () => fetchWithAuth(`${API_URL}/api/projects`),
    })
}

export function useCreateProject() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (data: { name: string; description: string }) =>
            fetchWithAuth(`${API_URL}/api/projects`, {
                method: 'POST',
                body: JSON.stringify(data),
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects'] })
        },
    })
}

export function useDeleteProject() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (id: string) =>
            fetchWithAuth(`${API_URL}/api/projects/${id}`, {
                method: 'DELETE',
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects'] })
        },
    })
}


// WebSocket connection for real-time logs
export function connectWebSocket(onMessage: (data: any) => void): WebSocket {
    const wsUrl = API_URL.replace('http', 'ws')
    const ws = new WebSocket(`${wsUrl}/ws`)

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        onMessage(data)
    }

    return ws
}
