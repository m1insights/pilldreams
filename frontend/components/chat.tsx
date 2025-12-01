"use client"

import { useState, useRef, useEffect } from "react"
import { X, Send, Sparkles, Loader2, MessageCircle } from "lucide-react"
import { aiApi } from "@/lib/api/client"
import type { ChatMessage } from "@/lib/api/types"

interface ChatProps {
  isOpen: boolean
  onClose: () => void
}

export function Chat({ isOpen, onClose }: ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = { role: "user", content: input.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setError(null)
    setIsLoading(true)

    try {
      const response = await aiApi.chat({
        question: input.trim(),
        conversation_history: messages,
      })

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.answer,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get response")
    } finally {
      setIsLoading(false)
    }
  }

  const suggestedQuestions = [
    "What is Vorinostat used for?",
    "Compare HDAC inhibitors to BET inhibitors",
    "List approved epigenetic drugs",
    "What makes EZH2 a good cancer target?",
  ]

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Chat Panel */}
      <div className="relative w-full max-w-lg bg-[#0a0a0a] border-l border-[#222] flex flex-col h-full animate-slide-in-right">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#222]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">Epigenetics AI</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[#1a1a1a] text-zinc-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <Sparkles className="w-12 h-12 text-blue-400/50 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">
                Ask about epigenetic oncology
              </h3>
              <p className="text-sm text-zinc-500 mb-6">
                I can explain drug scores, compare targets, and answer questions
                about our database.
              </p>

              {/* Suggested Questions */}
              <div className="space-y-2">
                {suggestedQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(q)}
                    className="w-full text-left px-4 py-2 rounded-lg bg-[#111] hover:bg-[#1a1a1a] text-sm text-zinc-300 hover:text-white border border-[#222] hover:border-[#333] transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg px-4 py-3 ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-[#1a1a1a] text-zinc-200 border border-[#222]"
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-[#1a1a1a] border border-[#222] rounded-lg px-4 py-3">
                    <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                  </div>
                </div>
              )}

              {error && (
                <div className="flex justify-center">
                  <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg px-4 py-2 text-sm">
                    {error}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-[#222]">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about drugs, targets, or scores..."
              className="flex-1 bg-[#111] border border-[#222] rounded-lg px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500/50 text-sm"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 disabled:cursor-not-allowed rounded-lg text-white transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-xs text-zinc-600 mt-2 text-center">
            Powered by Gemini AI. Responses are grounded in our database.
          </p>
        </form>
      </div>
    </div>
  )
}

// Chat Toggle Button (for navbar)
export function ChatButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-blue-600/20 to-blue-500/10 border border-blue-500/30 hover:border-blue-400/50 text-blue-400 hover:text-blue-300 transition-all"
    >
      <MessageCircle className="w-4 h-4" />
      <span className="text-sm font-medium">Ask AI</span>
    </button>
  )
}
