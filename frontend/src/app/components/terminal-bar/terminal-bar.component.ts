import { Component, Input } from '@angular/core';
import { AppMode } from '../../core/services/keyboard.service';

@Component({
  selector: 'app-terminal-bar',
  standalone: true,
  imports: [],
  template: `
    <footer class="terminal-bar">
      <div class="bar-item brand"><span class="status-dot"></span> ULTRON <span class="muted">/ TUTOR</span></div>
      <div class="bar-item"><span aria-hidden="true">◈</span> {{ engine }}</div>
      <div class="bar-item"><span aria-hidden="true">⌁</span> {{ model }}</div>
      <div class="bar-spacer"></div>
      <div class="bar-item"><span aria-hidden="true">⌨</span> {{ mode }}</div>
      <div class="bar-item connection" [class.offline]="!connected"><span aria-hidden="true">{{ connected ? '●' : '○' }}</span> {{ connected ? 'LINKED' : 'OFFLINE' }}</div>
      <div class="bar-item muted">MEM 42%</div>
    </footer>
  `,
})
export class TerminalBarComponent {
  @Input() engine = 'LOCAL';
  @Input() model = 'QWEN3-8B';
  @Input() mode: AppMode = 'NORMAL';
  @Input() connected = false;
}
