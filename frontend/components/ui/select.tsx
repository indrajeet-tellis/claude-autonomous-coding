'use client'

import * as React from 'react'

interface SelectProps {
    value: string
    onValueChange: (value: string) => void
    children: React.ReactNode
}

interface SelectContextValue {
    value: string
    onValueChange: (value: string) => void
    open: boolean
    setOpen: (open: boolean) => void
}

const SelectContext = React.createContext<SelectContextValue | undefined>(undefined)

export function Select({ value, onValueChange, children }: SelectProps) {
    const [open, setOpen] = React.useState(false)

    return (
        <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>
            <div className="relative inline-block">
                {children}
            </div>
        </SelectContext.Provider>
    )
}

export function SelectTrigger({ children, className = '' }: { children: React.ReactNode; className?: string }) {
    const context = React.useContext(SelectContext)
    if (!context) throw new Error('SelectTrigger must be used within Select')

    return (
        <button
            type="button"
            onClick={() => context.setOpen(!context.open)}
            className={`flex items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${className}`}
        >
            {children}
            <svg className="h-4 w-4 opacity-50 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
        </button>
    )
}

export function SelectValue({ placeholder }: { placeholder?: string }) {
    const context = React.useContext(SelectContext)
    if (!context) throw new Error('SelectValue must be used within Select')

    return <span>{context.value || placeholder}</span>
}

export function SelectContent({ children }: { children: React.ReactNode }) {
    const context = React.useContext(SelectContext)
    if (!context) throw new Error('SelectContent must be used within Select')

    if (!context.open) return null

    return (
        <>
            <div
                className="fixed inset-0 z-40"
                onClick={() => context.setOpen(false)}
            />
            <div className="absolute z-50 mt-1 min-w-[180px] rounded-md border bg-popover p-1 text-popover-foreground shadow-md animate-in fade-in-80">
                {children}
            </div>
        </>
    )
}

export function SelectItem({ value, children }: { value: string; children: React.ReactNode }) {
    const context = React.useContext(SelectContext)
    if (!context) throw new Error('SelectItem must be used within Select')

    return (
        <div
            className={`relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground ${context.value === value ? 'bg-accent' : ''
                }`}
            onClick={() => {
                context.onValueChange(value)
                context.setOpen(false)
            }}
        >
            {children}
        </div>
    )
}
