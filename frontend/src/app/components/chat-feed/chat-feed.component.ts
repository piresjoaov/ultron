import { AfterViewChecked, Component, ElementRef, Input, QueryList, ViewChild, ViewChildren, effect } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ChatMessage } from '../../core/models/message.model';
import { MathRendererComponent } from '../renderers/math-renderer.component';
import { SvgRendererComponent } from '../renderers/svg-renderer.component';
import { VideoRendererComponent } from '../renderers/video-renderer.component';
import { WebglRendererComponent } from '../renderers/webgl-renderer.component';
import { KeyboardService } from '../../core/services/keyboard.service';

@Component({
  selector: 'app-chat-feed',
  standalone: true,
  imports: [DatePipe, MathRendererComponent, SvgRendererComponent, VideoRendererComponent, WebglRendererComponent],
  template: `
    <main #scrollContainer class="chat-feed flex flex-col gap-4 overflow-y-auto p-4 h-full" aria-live="polite">
      @if (!messages.length) {
        <section class="empty-state">
          <div class="empty-mark">[ U ]</div>
          <h1>Ready when you are.</h1>
          <p>Ask a question, inspect a diagram, or work through a problem.</p>
        </section>
      }
      @for (message of messages; track message.id; let index = $index) {
        <div class="flex w-full" [class.justify-end]="message.sender === 'user'" [class.justify-start]="message.sender === 'ultron'">
          <article [class]="message.sender === 'user'
            ? 'message-card max-w-[80%] rounded-lg p-3 bg-cyan-950/40 border border-cyan-500/40 text-cyan-100 font-mono text-sm shadow-md'
            : 'message-card max-w-[85%] rounded-lg p-4 bg-slate-900/80 border border-emerald-500/40 text-slate-100 font-mono text-sm shadow-lg'"
            [class.selected]="index === selectedIndex" [class.user-message]="message.sender === 'user'"
            [class.system-critical]="isSystemCritical(message.content)">
            <div class="message-meta" [class.justify-end]="message.sender === 'user'"><span class="sender">[{{ message.sender === 'user' ? 'USER' : 'ULTRON' }}]</span><span>{{ message.timestamp | date:'HH:mm:ss' }}</span><span class="message-index">#{{ (index + 1).toString().padStart(2, '0') }}</span>@if (message.isStreaming) { <span class="cursor" aria-label="Streaming"></span> }</div>
            <div class="message-body"><p>{{ cleanContent(message.content) }}</p>
              @if (message.media?.type === 'math') { <app-math-renderer [formula]="message.media?.payload ?? ''" /> }
              @if (message.media?.type === 'svg_diagram') { <app-svg-renderer [rawSvg]="message.media?.payload ?? ''" /> }
              @if (message.media?.type === 'manim_video') { <app-video-renderer [source]="message.media?.payload ?? ''" /> }
              @if (message.media?.type === 'webgl_3d') { <app-webgl-renderer [sceneData]="message.media?.payload ?? ''" /> }
            </div>
          </article>
        </div>
      }
      @if (streaming) { <div class="streaming-line"><span class="pulse"></span> generating response<span class="cursor"></span></div> }
    </main>
  `,
})
export class ChatFeedComponent implements AfterViewChecked {
  private readonly systemCriticalMarker = '[[ULTRON_SYSTEM_HEALTH_RED]]';
  @Input() messages: ChatMessage[] = [];
  @Input() selectedIndex = 0;
  @Input() streaming = false;

  isSystemCritical(content: string): boolean {
    return content.includes(this.systemCriticalMarker);
  }

  cleanContent(content: string): string {
    return content.replace(this.systemCriticalMarker, '').trim();
  }

  @ViewChildren(VideoRendererComponent) private videoPlayers!: QueryList<VideoRendererComponent>;
  @ViewChild('scrollContainer') private scrollContainer?: ElementRef<HTMLElement>;
  private lastScrollKey = '';

  constructor(private readonly keyboard: KeyboardService) {
    effect(() => {
      this.keyboard.videoToggleRequested();
      const selected = this.messages[this.selectedIndex];
      if (selected?.media?.type !== 'manim_video') return;
      const videoIndex = this.messages.slice(0, this.selectedIndex)
        .filter((message) => message.media?.type === 'manim_video').length;
      this.videoPlayers.get(videoIndex)?.togglePlayback();
    });
  }

  ngAfterViewChecked(): void {
    const lastMessage = this.messages[this.messages.length - 1];
    const scrollKey = `${this.messages.length}:${lastMessage?.id ?? ''}:${lastMessage?.content.length ?? 0}:${lastMessage?.isStreaming ?? false}`;
    if (scrollKey === this.lastScrollKey) return;
    this.lastScrollKey = scrollKey;
    queueMicrotask(() => this.scrollContainer?.nativeElement.scrollTo({ top: this.scrollContainer.nativeElement.scrollHeight, behavior: 'smooth' }));
  }
}
