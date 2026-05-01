import { useState, useEffect } from 'react';

export const useKernelTelemetry = (wsUrl: string) => {
  const [telemetry, setTelemetry] = useState<any[]>([]);
  const [status, setStatus] = useState<'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => setStatus('connected');
    socket.onclose = () => setStatus('disconnected');
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setTelemetry((prev) => [data, ...prev].slice(0, 100));
    };

    return () => socket.close();
  }, [wsUrl]);

  return { telemetry, status };
};
