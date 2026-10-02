import { Component, Input } from '@angular/core';
import { NgxKatexComponent } from 'ngx-katex';

@Component({
  selector: 'app-math-renderer',
  standalone: true,
  imports: [NgxKatexComponent],
  template: `<div class="math-output"><ngx-katex [equation]="formula"></ngx-katex></div>`,
})
export class MathRendererComponent {
  @Input() formula = '';
}
