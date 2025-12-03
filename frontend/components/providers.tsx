"use client"

import { ReactNode } from "react"
import { ChatProvider } from "./chat-provider"
import { AuthProvider } from "@/lib/auth/context"

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <ChatProvider>{children}</ChatProvider>
    </AuthProvider>
  )
}
