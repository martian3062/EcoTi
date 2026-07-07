export type FeedMessage = {
  kind: "hello" | "event" | "fused" | "toast";
  data: Record<string, unknown>;
};

export function connectFeed(onMessage: (m: FeedMessage) => void): () => void {
  const base = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000";
  let socket: WebSocket | null = null;
  let closed = false;
  let retry: ReturnType<typeof setTimeout>;

  const open = () => {
    socket = new WebSocket(`${base}/ws/feed`);
    socket.onmessage = (e) => {
      try {
        onMessage(JSON.parse(e.data) as FeedMessage);
      } catch {
        /* ignore */
      }
    };
    socket.onclose = () => {
      if (!closed) retry = setTimeout(open, 2000);
    };
  };
  open();

  return () => {
    closed = true;
    clearTimeout(retry);
    socket?.close();
  };
}
