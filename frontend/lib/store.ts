import { create } from 'zustand'
import { Task, Log, AgentStatus } from './schemas'

// Agent store
interface AgentState {
    status: AgentStatus | null
    currentTask: Task | null
    logs: Log[]
    setStatus: (status: AgentStatus) => void
    setCurrentTask: (task: Task | null) => void
    addLog: (log: Log) => void
    clearLogs: () => void
}

export const useAgentStore = create<AgentState>((set) => ({
    status: null,
    currentTask: null,
    logs: [],
    setStatus: (status) => set({ status }),
    setCurrentTask: (task) => set({ currentTask: task }),
    addLog: (log) => set((state) => ({ logs: [log, ...state.logs].slice(0, 500) })),
    clearLogs: () => set({ logs: [] }),
}))

// UI store
interface UIState {
    isHeadless: boolean
    vncUrl: string
    setHeadless: (value: boolean) => void
    setVncUrl: (url: string) => void
}

export const useUIStore = create<UIState>((set) => ({
    isHeadless: false,
    vncUrl: process.env.NEXT_PUBLIC_VNC_URL || 'http://localhost:6080/vnc.html',
    setHeadless: (value) => set({ isHeadless: value }),
    setVncUrl: (url) => set({ vncUrl: url }),
}))

// Auth store
interface AuthState {
    isAuthenticated: boolean
    username: string | null
    setAuthenticated: (value: boolean, username?: string) => void
    logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
    isAuthenticated: false,
    username: null,
    setAuthenticated: (value, username) => set({ isAuthenticated: value, username: username || null }),
    logout: () => set({ isAuthenticated: false, username: null }),
}))
