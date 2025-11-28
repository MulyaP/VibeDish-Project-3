"use client"

import React from "react"
import type { ChatMessage } from "@/hooks/useChat"
import Avatar from "./Avatar"

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
    <aside className="w-80 border-r bg-gray-50 h-[600px] overflow-auto">
      <div className="p-4 border-b flex items-center justify-between sticky top-0 bg-gray-50 z-10">
        <h3 className="text-sm font-semibold">Conversations</h3>
        <button className="text-sm text-blue-600 font-medium" onClick={onCreate} aria-label="Create new conversation">New</button>
      </div>
      <div>
        {sessions.length === 0 && (
          <div className="p-4 text-sm text-gray-500">No conversations yet</div>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`w-full p-3 border-b hover:bg-gray-100 flex items-center gap-3 ${selectedId === s.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''}`}
          >
            <button className="flex items-center gap-3 text-left flex-1" onClick={() => onSelect(s.id)}>
              <Avatar name={s.title || 'Chat'} size={36} />
              <div className="truncate">
                <div className="font-medium truncate text-sm">{s.title || 'Untitled'}</div>
                {s.last_message && <div className="text-xs text-gray-500 truncate">{s.last_message.content.slice(0, 60)}</div>}
              </div>
            </button>

            <div className="flex items-center gap-1">
              <button
                title="Rename"
                className="text-sm text-gray-600 px-2"
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
        ))}
      </div>
    </aside>
  )
}
