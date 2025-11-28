"use client"

import React, { useState } from "react"
import useChat from "../../hooks/useChat"
import MessageList from "./MessageList"

export default function ChatWindow() {
  const { messages, sendMessage, loading, error, sessionId, setSessionId } = useChat()
  const [text, setText] = useState("")

  async function onSend() {
    if (!text.trim()) return
    try {
      await sendMessage(text.trim())
      setText("")
    } catch (err) {
      // error handled in hook
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="border rounded-lg overflow-hidden shadow">
        <div className="h-96 overflow-auto bg-white">
          <MessageList messages={messages} />
        </div>
        <div className="p-3 bg-gray-50">
          {error && <div className="text-red-600 mb-2">{error}</div>}
          <div className="flex gap-2">
            <input
              className="flex-1 border rounded px-3 py-2"
              placeholder="Type a message..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  void onSend()
                }
              }}
            />
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
              onClick={() => void onSend()}
              disabled={loading}
            >
              {loading ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
