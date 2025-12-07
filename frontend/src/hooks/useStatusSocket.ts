import { useEffect, useState, useRef, useCallback } from 'react';

interface StatusEvent {
  event: string;
  session_id?: string;
  timestamp: number;
  data: Record<string, any>;
}

interface UseStatusSocketOptions {
  onEvent?: (event: StatusEvent) => void;
  autoConnect?: boolean;
}

export function useStatusSocket(options: UseStatusSocketOptions = {}) {
  const { onEvent, autoConnect = true } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<StatusEvent[]>([]);
  const [lastEvent, setLastEvent] = useState<StatusEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket('ws://localhost:8000/ws/status');

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data: StatusEvent = JSON.parse(event.data);
        setLastEvent(data);
        setEvents((prev) => [...prev.slice(-99), data]);
        onEvent?.(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [onEvent]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLastEvent(null);
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    events,
    lastEvent,
    connect,
    disconnect,
    clearEvents,
  };
}
