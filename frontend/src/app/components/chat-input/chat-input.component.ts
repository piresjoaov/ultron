import { AfterViewInit, Component, EventEmitter, Output, ViewChild, ElementRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { KeyboardService } from '../../core/services/keyboard.service';

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [FormsModule],
  template: `
    <form class="chat-input" (submit)="submit($event)">
      <span class="prompt">ultron <b>></b></span>
      <textarea #input [(ngModel)]="value" name="prompt" rows="1" placeholder="Ask Ultron anything..." autocomplete="off" (focus)="keyboard.enterInsertMode()" (keydown.enter)="handleEnter($event)"></textarea>
      <span class="input-hint">{{ keyboard.appMode() === 'INSERT' ? 'INSERT' : 'PRESS I TO TYPE' }}</span>
    </form>
  `,
})
export class ChatInputComponent implements AfterViewInit {
  @Output() submitted = new EventEmitter<string>();
  @ViewChild('input') private input?: ElementRef<HTMLTextAreaElement>;
  value = '';

  constructor(public readonly keyboard: KeyboardService) {}

  ngAfterViewInit(): void {
    if (this.input) this.keyboard.registerInput(this.input.nativeElement);
  }

  submit(event: Event): void {
    event.preventDefault();
    this.sendCurrentValue();
  }

  handleEnter(event: Event): void {
    const keyboardEvent = event as KeyboardEvent;
    if (keyboardEvent.shiftKey) return;
    keyboardEvent.preventDefault();
    this.sendCurrentValue();
  }

  private sendCurrentValue(): void {
    const content = this.value.trim();
    if (!content) return;
    this.submitted.emit(content);
    this.value = '';
  }
}
