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

    // Get token for authentication
    const token = localStorage.getItem("access_token");
    if (!token) {
      console.warn("[WebSocket] No access token found, skipping connection");
      return;
    }

    // WebSocket URL with token as query param
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
    const wsUrlWithToken = `${wsUrl}?token=${encodeURIComponent(token)}`;
    
    try {
      const ws = new WebSocket(wsUrlWithToken);

      ws.onopen = () => {
        console.log("[WebSocket] Connected");
        setConnected(true);
        reconnectAttemptsRef.current = 0;
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
    // Try initial connection
    connect();

    // Listen for storage events (token added from another tab)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "access_token" && e.newValue) {
        console.log("[WebSocket] Token detected, attempting connection");
        connect();
      } else if (e.key === "access_token" && !e.newValue) {
        // Token removed (logout)
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
          setConnected(false);
        }
      }
    };

    // Custom event listener untuk token changes dalam same tab
    const handleTokenChange = () => {
      const token = localStorage.getItem("access_token");
      if (token && !wsRef.current) {
        console.log("[WebSocket] Token change detected, connecting");
        connect();
      }
    };

    window.addEventListener("storage", handleStorageChange);
    window.addEventListener("auth-token-changed", handleTokenChange);

    // Poll untuk token availability (fallback jika event tidak fire)
    const pollInterval = setInterval(() => {
      const token = localStorage.getItem("access_token");
      if (token && !wsRef.current) {
        connect();
        clearInterval(pollInterval); // Stop polling setelah connect
      }
    }, 1000);

    // Cleanup on unmount
    return () => {
      clearInterval(pollInterval);
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("auth-token-changed", handleTokenChange);
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
