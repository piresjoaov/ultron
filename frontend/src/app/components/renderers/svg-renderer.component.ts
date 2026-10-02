import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-svg-renderer',
  standalone: true,
  template: `
    <div class="svg-viewport" (wheel)="zoom($event)">
      <div class="svg-content" [style.transform]="'scale(' + scale + ')'" [innerHTML]="rawSvg"></div>
    </div>
  `,
})
export class SvgRendererComponent {
  @Input() rawSvg = '';
  scale = 1;

  zoom(event: WheelEvent): void {
    event.preventDefault();
    this.scale = Math.min(3, Math.max(0.5, this.scale + (event.deltaY < 0 ? 0.1 : -0.1)));
  }
}
