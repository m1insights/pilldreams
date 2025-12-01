"use client"

import { ReactNode } from "react"
import { ChatProvider } from "./chat-provider"

export function Providers({ children }: { children: ReactNode }) {
  return <ChatProvider>{children}</ChatProvider>
}
