"use client"

import { useState, useEffect, useCallback } from "react"
import { authenticatedFetch } from "@/context/auth-context"

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "")

export type ChatMessage = {
	id?: string
	role: "user" | "assistant"
	content: string
	created_at?: string
}

export function useChat(initialSessionId?: string | null) {
	const [sessionId, setSessionId] = useState<string | null>(typeof window !== "undefined" ? (initialSessionId || localStorage.getItem("chat_session_id")) : initialSessionId || null)
	const [messages, setMessages] = useState<ChatMessage[]>([])
		const [sessions, setSessions] = useState<any[]>([])
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)

	useEffect(() => {
		if (sessionId) {
			try {
				localStorage.setItem("chat_session_id", sessionId)
			} catch (_) {}
			void loadHistory(sessionId)
		}
	}, [sessionId])

	const loadHistory = useCallback(async (sid: string) => {
		setLoading(true)
		setError(null)
		try {
			const resp = await authenticatedFetch(`${API_BASE}/chat/history?session_id=${encodeURIComponent(sid)}`)
			if (!resp.ok) throw new Error("Failed to load history")
			const data = await resp.json()
			setMessages(data.messages || [])
		} catch (err: any) {
			setError(err?.message || String(err))
		} finally {
			setLoading(false)
		}
	}, [])

	const sendMessage = useCallback(async (text: string, context?: Record<string, any>) => {
		setLoading(true)
		setError(null)
		try {
			const body = { session_id: sessionId, message: text, context }
			const resp = await authenticatedFetch(`${API_BASE}/chat/messages`, {
				method: "POST",
				body: JSON.stringify(body),
			})

			if (!resp.ok) {
				const err = await resp.json().catch(() => ({}))
				throw new Error(err.detail || `Send failed (${resp.status})`)
			}

			const data = await resp.json()

			const assistantMsg: ChatMessage = { id: data.message_id, role: "assistant", content: data.reply }
			const userMsg: ChatMessage = { role: "user", content: text }
			setMessages((m) => [...m, userMsg, assistantMsg])

			if (data.session_id && data.session_id !== sessionId) {
				setSessionId(data.session_id)
				try {
					localStorage.setItem("chat_session_id", data.session_id)
				} catch (_) {}
			}

			return data
		} catch (err: any) {
			setError(err?.message || String(err))
			throw err
		} finally {
			setLoading(false)
		}
	}, [sessionId])

	const createNewSession = useCallback(() => {
		const sid = (typeof crypto !== "undefined" && (crypto as any).randomUUID) ? (crypto as any).randomUUID() : `s-${Date.now()}`
		setSessionId(sid)
		try {
			localStorage.setItem("chat_session_id", sid)
		} catch (_) {}
		return sid
	}, [])

		const loadSessions = useCallback(async () => {
			try {
				const resp = await authenticatedFetch(`${API_BASE}/chat/sessions`)
				if (!resp.ok) throw new Error('Failed to load sessions')
				const data = await resp.json()
				setSessions(data.sessions || [])
				return data.sessions || []
			} catch (err) {
				// ignore for now
				return []
			}
		}, [])

	return {
		sessionId,
		setSessionId,
		messages,
			sessions,
		loading,
		error,
		sendMessage,
		loadHistory,
		createNewSession,
			loadSessions,
	}
}

export default useChat

