import { Component, ElementRef, Input, ViewChild } from '@angular/core';

@Component({
  selector: 'app-video-renderer',
  standalone: true,
  template: `
    <div class="video-frame">
      <video #player [src]="source" controls preload="metadata"></video>
      <span class="media-label">MANIM / ANIMATION</span>
    </div>
  `,
})
export class VideoRendererComponent {
  @Input() source = '';
  @ViewChild('player') private player?: ElementRef<HTMLVideoElement>;

  togglePlayback(): void {
    const video = this.player?.nativeElement;
    if (!video) return;
    video.paused ? void video.play() : video.pause();
  }
}
