import { Injectable, signal } from '@angular/core';
import { ChatMedia, ChatMessage } from '../models/message.model';

@Injectable({ providedIn: 'root' })
export class WebsocketService {
  readonly messages = signal<ChatMessage[]>([]);
  readonly connected = signal(false);
  readonly streaming = signal(false);

  private socket?: WebSocket;
  private socketUrl = 'ws://localhost:8000/ws/chat';
  private reconnectTimer?: ReturnType<typeof setTimeout>;
  private activeAiMessageId?: string;
  private pendingPrompt?: string;

  connect(url = 'ws://localhost:8000/ws/chat'): void {
    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) return;
    this.socketUrl = url;
    this.socket = new WebSocket(url);
    this.socket.onopen = () => {
      this.connected.set(true);
      if (this.pendingPrompt) {
        this.sendPayload(this.pendingPrompt);
        this.pendingPrompt = undefined;
      }
    };
    this.socket.onclose = () => {
      this.connected.set(false);
      this.streaming.set(false);
      this.reconnectTimer = setTimeout(() => this.connect(this.socketUrl), 1000);
    };
    this.socket.onerror = () => this.connected.set(false);
    this.socket.onmessage = (event) => this.handlePayload(event.data);
  }

  sendMessage(prompt: string): void {
    const content = prompt.trim();
    if (!content) return;

    const timestamp = new Date().toLocaleTimeString();
    const aiMessageId = `${Date.now()}-ultron`;
    this.activeAiMessageId = aiMessageId;
    this.messages.update((messages) => [...messages,
      { id: Date.now().toString(), sender: 'user', content, timestamp },
      { id: aiMessageId, sender: 'ultron', content: '', timestamp, isStreaming: true },
    ]);
    this.streaming.set(true);

    if (this.socket?.readyState === WebSocket.OPEN) {
      this.sendPayload(content);
    } else {
      this.pendingPrompt = content;
      this.connect();
    }
  }

  clear(): void {
    this.messages.set([]);
    this.streaming.set(false);
    this.activeAiMessageId = undefined;
    this.pendingPrompt = undefined;
  }

  private handlePayload(raw: string): void {
    try {
      const payload = JSON.parse(raw) as {
        type?: 'chunk' | 'done' | 'media';
        content?: string;
        media?: ChatMedia;
      };
      const messageId = this.activeAiMessageId;
      if (!messageId) return;

      if (payload.type === 'chunk') {
        this.messages.update((messages) => messages.map((message) => message.id === messageId
          ? { ...message, content: message.content + (payload.content ?? ''), isStreaming: true }
          : message));
      } else if (payload.type === 'media' && payload.media) {
        this.messages.update((messages) => messages.map((message) => message.id === messageId
          ? { ...message, media: payload.media }
          : message));
      } else if (payload.type === 'done') {
        this.messages.update((messages) => messages.map((message) => message.id === messageId
          ? { ...message, isStreaming: false }
          : message));
        this.streaming.set(false);
        this.activeAiMessageId = undefined;
      }
    } catch {
      const messageId = this.activeAiMessageId;
      if (messageId) {
        this.messages.update((messages) => messages.map((message) => message.id === messageId
          ? { ...message, content: message.content + raw, isStreaming: false }
          : message));
      }
      this.streaming.set(false);
    }
  }

  private sendPayload(content: string): void {
    this.socket?.send(JSON.stringify({ type: 'prompt', content }));
  }
}
