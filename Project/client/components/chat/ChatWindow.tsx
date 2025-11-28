"use client"

import React, { useState, useEffect } from "react"
import useChat from "../../hooks/useChat"
import MessageList from "./MessageList"
import SessionList from "./SessionList"

export default function ChatWindow() {
  const { messages, sendMessage, loading, error, sessionId, setSessionId, sessions, loadSessions, createNewSession, loadHistory, createSession, renameSession, deleteSession } = useChat()
  const [text, setText] = useState("")

  useEffect(() => {
    void loadSessions()
  }, [loadSessions])

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
    <div className="max-w-5xl mx-auto p-4">
      <div className="border rounded-lg overflow-hidden shadow flex">
        <SessionList
          sessions={sessions}
          selectedId={sessionId}
          onSelect={(id: string) => {
            setSessionId(id)
            void loadHistory(id)
          }}
          onCreate={async () => {
            try {
              // create on server without a default title so server can auto-generate
              const sid = await createSession()
              if (sid) {
                setSessionId(sid)
                // history will be empty for new session
              }
            } catch (err) {
              // fallback to local session
              const sid = createNewSession()
              setSessionId(sid)
            }
          }}
          onRename={async (id: string, title?: string) => {
            try {
              await renameSession(id, title)
            } catch (err) {
              // ignore
            }
          }}
          onDelete={async (id: string) => {
            try {
              await deleteSession(id)
              // if current session deleted, clear selection handled by hook
            } catch (err) {
              // ignore
            }
          }}
        />
        <div className="flex-1">
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
    </div>
  )
}
