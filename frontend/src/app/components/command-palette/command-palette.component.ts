import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommandService } from '../../core/services/command.service';
import { KeyboardService } from '../../core/services/keyboard.service';

@Component({
  selector: 'app-command-palette',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="palette-backdrop" (click)="close()">
      <section class="command-palette" (click)="$event.stopPropagation()">
        <div class="palette-heading"><span class="palette-symbol">:</span><span>COMMAND PALETTE</span><kbd>ESC</kbd></div>
        <input #command autofocus [(ngModel)]="value" placeholder="clear · config · engine · model" (keydown.enter)="run()" (keydown.escape)="close()" />
        <div class="palette-footer"><span>ENTER to execute</span><span>CTRL+P to toggle</span></div>
      </section>
    </div>
  `,
})
export class CommandPaletteComponent {
  @Output() executed = new EventEmitter<string>();
  value = '';

  constructor(private readonly keyboard: KeyboardService, private readonly commands: CommandService) {}

  run(): void {
    if (!this.value.trim()) return;
    const result = this.commands.execute(this.value);
    this.executed.emit(result.message ?? `${result.engine ?? result.model ?? 'Command'} selected`);
    this.close();
  }

  close(): void {
    this.keyboard.closeCommandPalette();
  }
}
