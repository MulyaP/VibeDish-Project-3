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
    <div className="max-w-6xl mx-auto p-6">
      <div className="rounded-2xl overflow-hidden shadow-xl flex bg-white">
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
        <div className="flex-1 flex flex-col">
          <div className="flex-1 h-[600px] overflow-auto bg-gradient-to-b from-gray-50 to-white">
            <MessageList messages={messages} />
          </div>

          <div className="p-4 bg-white border-t">
            {error && <div className="text-red-600 mb-2">{error}</div>}
            <div className="flex items-center gap-3">
              <textarea
                rows={1}
                className="flex-1 resize-none rounded-full border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 placeholder-gray-400"
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
                className="flex items-center justify-center w-12 h-12 rounded-full bg-blue-600 text-white shadow-md disabled:opacity-50"
                onClick={() => void onSend()}
                disabled={loading}
                aria-label="Send message"
              >
                {loading ? (
                  <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" />
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
