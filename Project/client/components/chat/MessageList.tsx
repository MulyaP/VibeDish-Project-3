"use client"

import React from "react"
import type { ChatMessage } from "../../hooks/useChat"

export function MessageList({ messages }: { messages: ChatMessage[] }) {
  return (
    <div className="space-y-3 p-4">
      {messages.map((m, idx) => (
        <div key={m.id || idx} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
          <div className={`max-w-[70%] rounded-lg p-3 ${m.role === "user" ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-900"}`}>
            <div className="whitespace-pre-wrap">{m.content}</div>
            {m.created_at && <div className="text-xs text-gray-400 mt-1">{new Date(m.created_at).toLocaleString()}</div>}
          </div>
        </div>
      ))}
    </div>
  )
}

export default MessageList
