import React from "react"
import ChatWindow from "@/components/chat/ChatWindow"

export default function ChatPage() {
  return (
    <div className="py-8">
      <h1 className="text-2xl font-semibold text-center mb-4">Chat with VibeDish</h1>
      <ChatWindow />
    </div>
  )
}
