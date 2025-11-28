"use client"

import React from "react"
import type { ChatMessage } from "@/hooks/useChat"

type Session = {
  id: string
  title?: string | null
  metadata?: any
  created_at?: string
  last_message?: ChatMessage | null
}

export default function SessionList({
  sessions,
  selectedId,
  onSelect,
  onCreate,
  onRename,
  onDelete,
}: {
  sessions: Session[]
  selectedId?: string | null
  onSelect: (id: string) => void
  onCreate: () => void
  onRename?: (id: string, title?: string) => void
  onDelete?: (id: string) => void
}) {
  return (
    <aside className="w-72 border-r bg-gray-50 h-[600px] overflow-auto">
      <div className="p-3 border-b flex items-center justify-between">
        <h3 className="text-sm font-semibold">Conversations</h3>
        <button className="text-sm text-primary" onClick={onCreate}>New</button>
      </div>
      <div>
        {sessions.length === 0 && (
          <div className="p-4 text-sm text-muted-foreground">No conversations yet</div>
        )}
        {sessions.map((s) => (
          <div key={s.id} className={`w-full p-3 border-b hover:bg-gray-100 ${selectedId === s.id ? 'bg-white' : ''}`}>
            <div className="flex items-start justify-between gap-2">
              <button className="text-left flex-1" onClick={() => onSelect(s.id)}>
                <div className="font-medium truncate">{s.title || 'Untitled'}</div>
                <div className="text-xs text-muted-foreground truncate">
                  {s.last_message ? s.last_message.content : 'No messages yet'}
                </div>
              </button>
              <div className="flex items-center gap-1">
                <button
                  title="Rename"
                  className="text-sm text-muted-foreground px-2"
                  onClick={() => {
                    const newTitle = window.prompt('Rename conversation', s.title || '')
                    if (newTitle !== null && typeof onRename === 'function') {
                      onRename(s.id, newTitle)
                    }
                  }}
                >
                  ✏️
                </button>
                <button
                  title="Delete"
                  className="text-sm text-red-500 px-2"
                  onClick={() => {
                    const ok = window.confirm('Delete this conversation? This cannot be undone.')
                    if (ok && typeof onDelete === 'function') onDelete(s.id)
                  }}
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}
