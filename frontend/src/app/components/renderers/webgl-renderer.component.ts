import { AfterViewInit, Component, ElementRef, Input, ViewChild } from '@angular/core';

@Component({
  selector: 'app-webgl-renderer',
  standalone: true,
  template: `<div class="webgl-frame"><canvas #canvas></canvas><span class="media-label">WEBGL / MOLECULE</span></div>`,
})
export class WebglRendererComponent implements AfterViewInit {
  @Input() sceneData = '';
  @ViewChild('canvas') private canvas?: ElementRef<HTMLCanvasElement>;

  ngAfterViewInit(): void {
    const context = this.canvas?.nativeElement.getContext('webgl2') ?? this.canvas?.nativeElement.getContext('webgl');
    if (!context) return;
    context.clearColor(0.025, 0.04, 0.055, 1);
    context.clear(context.COLOR_BUFFER_BIT);
  }
}
