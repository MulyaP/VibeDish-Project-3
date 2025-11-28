"use client"

import React, { useEffect } from "react"
import ChatWindow from "@/components/chat/ChatWindow"
import { useAuth } from "@/context/auth-context"
import { useRouter } from "next/navigation"

export default function ChatPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Redirect unauthenticated users to the login page and preserve the intended path
      const next = encodeURIComponent("/chat")
      router.push(`/login?next=${next}`)
    }
  }, [isAuthenticated, isLoading, router])

  if (!isAuthenticated) {
    return (
      <div className="py-8 text-center">
        <p className="text-gray-600">Redirecting to login...</p>
      </div>
    )
  }

  return (
    <div className="py-8">
      <h1 className="text-2xl font-semibold text-center mb-4">Chat with VibeDish</h1>
      <ChatWindow />
    </div>
  )
}
