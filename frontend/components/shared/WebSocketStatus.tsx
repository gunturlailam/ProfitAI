"use client";

import { Wifi, WifiOff } from "lucide-react";
import { useWebSocket } from "@/lib/websocket-context";

export function WebSocketStatus() {
  const { connected } = useWebSocket();

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 px-3 py-2 rounded-lg shadow-lg border flex items-center gap-2 text-sm font-medium transition-all ${
        connected
          ? "bg-green-50 border-green-200 text-green-800"
          : "bg-red-50 border-red-200 text-red-800"
      }`}
    >
      {connected ? (
        <>
          <Wifi className="w-4 h-4" />
          <span>Real-time Active</span>
        </>
      ) : (
        <>
          <WifiOff className="w-4 h-4" />
          <span>Disconnected</span>
        </>
      )}
    </div>
  );
}
