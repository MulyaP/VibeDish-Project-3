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
}: {
  sessions: Session[]
  selectedId?: string | null
  onSelect: (id: string) => void
  onCreate: () => void
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
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`w-full text-left p-3 border-b hover:bg-gray-100 ${selectedId === s.id ? 'bg-white' : ''}`}
          >
            <div className="font-medium truncate">{s.title || 'Untitled'}</div>
            <div className="text-xs text-muted-foreground truncate">
              {s.last_message ? s.last_message.content : 'No messages yet'}
            </div>
          </button>
        ))}
      </div>
    </aside>
  )
}
