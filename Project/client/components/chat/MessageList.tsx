"use client"

import React, { useEffect, useRef } from "react"
import type { ChatMessage } from "../../hooks/useChat"
import Avatar from "./Avatar"

export function MessageList({ messages }: { messages: ChatMessage[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const el = containerRef.current
    if (el) {
      // scroll to bottom smoothly when messages change
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" })
    }
  }, [messages])

  return (
    <div ref={containerRef} className="p-4 space-y-4 h-full">
      {messages.map((m, idx) => (
        <div key={m.id || idx} className={`flex items-end gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
          {m.role === "assistant" && (
            <div className="flex-shrink-0">
              <Avatar name="Bot" size={36} />
            </div>
          )}

          <div className={`relative max-w-[75%] break-words p-3 rounded-2xl shadow-sm ${
            m.role === "user" ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white" : "bg-white text-gray-900 border"
          }`}>
            <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
            {m.created_at && <div className="text-[11px] text-gray-400 mt-2 text-right">{new Date(m.created_at).toLocaleTimeString()}</div>}
          </div>

          {m.role === "user" && (
            <div className="flex-shrink-0">
              <Avatar name="You" size={36} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default MessageList
