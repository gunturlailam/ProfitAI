"use client";

import { createContext, useContext, useEffect, useRef, useState, ReactNode } from "react";
import { toast } from "./toast";

interface WebSocketMessage {
  type: string;
  data: any;
}

interface WebSocketContextType {
  connected: boolean;
  sendMessage: (message: any) => void;
  subscribe: (type: string, callback: (data: any) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within WebSocketProvider");
  }
  return context;
}

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const subscribersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 3000;

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // WebSocket URL from environment or default
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
    
    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("[WebSocket] Connected");
        setConnected(true);
        reconnectAttemptsRef.current = 0;
        
        // Authenticate if token available
        const token = localStorage.getItem("access_token");
        if (token) {
          ws.send(JSON.stringify({ type: "auth", token }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log("[WebSocket] Message received:", message.type);

          // Notify subscribers
          const callbacks = subscribersRef.current.get(message.type);
          if (callbacks) {
            callbacks.forEach((callback) => callback(message.data));
          }

          // Handle specific message types
          handleMessage(message);
        } catch (error) {
          console.error("[WebSocket] Parse error:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
      };

      ws.onclose = () => {
        console.log("[WebSocket] Disconnected");
        setConnected(false);
        wsRef.current = null;

        // Auto-reconnect
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current++;
          console.log(
            `[WebSocket] Reconnecting... (attempt ${reconnectAttemptsRef.current})`
          );
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY);
        } else {
          toast.warning(
            "Koneksi Real-time Terputus",
            "Refresh halaman untuk mencoba kembali.",
            { duration: 0 }
          );
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("[WebSocket] Connection error:", error);
    }
  };

  const handleMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case "ratio_alert":
        // Auto-show toast for new ratio alerts
        toast.error(
          message.data.title || "Peringatan Rasio",
          message.data.message || "Terjadi perubahan pada rasio keuangan",
          { duration: 10000 }
        );
        break;

      case "transaction_posted":
        toast.success(
          "Transaksi Tercatat",
          "Transaksi baru telah ditambahkan. Dashboard akan diperbarui.",
          { duration: 5000 }
        );
        break;

      case "balance_updated":
        toast.info(
          "Neraca Diperbarui",
          "Saldo neraca telah diupdate. Rasio akan dihitung ulang.",
          { duration: 5000 }
        );
        break;

      default:
        console.log(`[WebSocket] Unhandled message type: ${message.type}`);
    }
  };

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("[WebSocket] Cannot send message: not connected");
    }
  };

  const subscribe = (type: string, callback: (data: any) => void) => {
    if (!subscribersRef.current.has(type)) {
      subscribersRef.current.set(type, new Set());
    }
    subscribersRef.current.get(type)!.add(callback);

    // Return unsubscribe function
    return () => {
      subscribersRef.current.get(type)?.delete(callback);
    };
  };

  useEffect(() => {
    // Connect on mount
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const value: WebSocketContextType = {
    connected,
    sendMessage,
    subscribe,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}
