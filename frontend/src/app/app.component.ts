import { Component, effect } from '@angular/core';
import { ChatFeedComponent } from './components/chat-feed/chat-feed.component';
import { ChatInputComponent } from './components/chat-input/chat-input.component';
import { CommandPaletteComponent } from './components/command-palette/command-palette.component';
import { TerminalBarComponent } from './components/terminal-bar/terminal-bar.component';
import { KeyboardService } from './core/services/keyboard.service';
import { WebsocketService } from './core/services/websocket.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ChatFeedComponent, ChatInputComponent, CommandPaletteComponent, TerminalBarComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  notice = '';

  constructor(
    readonly keyboard: KeyboardService,
    readonly websocket: WebsocketService,
  ) {
    this.websocket.connect();
    effect(() => {
      this.keyboard.clearRequested();
      this.websocket.clear();
    }, { allowSignalWrites: true });
    effect(() => this.keyboard.setMessageCount(this.websocket.messages().length), { allowSignalWrites: true });
    effect(() => {
      this.keyboard.copyRequested();
      const selected = this.websocket.messages()[this.keyboard.selectedIndex()];
      if (selected) void navigator.clipboard?.writeText(selected.content);
    });
  }

  submitPrompt(prompt: string): void {
    this.websocket.sendMessage(prompt);
  }

  handleCommand(message: string): void {
    if (message === 'Terminal cleared') this.websocket.clear();
    this.notice = message;
    window.setTimeout(() => this.notice = '', 2400);
  }
}
