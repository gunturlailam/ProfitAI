"use client"

import { QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { queryClient } from "@/lib/query-client"
import { WebSocketProvider } from "@/lib/websocket-context"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        {children}
        {process.env.NEXT_PUBLIC_APP_ENV === "development" && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </WebSocketProvider>
    </QueryClientProvider>
  )
}
