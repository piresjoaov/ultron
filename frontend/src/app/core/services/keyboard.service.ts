import { DOCUMENT } from '@angular/common';
import { DestroyRef, Injectable, inject, signal } from '@angular/core';

export type AppMode = 'NORMAL' | 'INSERT' | 'COMMAND';

@Injectable({ providedIn: 'root' })
export class KeyboardService {
  private readonly document = inject(DOCUMENT);
  private readonly destroyRef = inject(DestroyRef);

  readonly appMode = signal<AppMode>('NORMAL');
  readonly selectedIndex = signal(0);
  readonly commandPaletteOpen = signal(false);
  readonly clearRequested = signal(0);
  readonly copyRequested = signal(0);
  readonly videoToggleRequested = signal(0);

  private messageCount = 0;
  private inputElement?: HTMLTextAreaElement;

  constructor() {
    const handler = (event: KeyboardEvent) => this.handleKeydown(event);
    this.document.addEventListener('keydown', handler);
    this.destroyRef.onDestroy(() => this.document.removeEventListener('keydown', handler));
  }

  registerInput(element: HTMLTextAreaElement): void {
    this.inputElement = element;
  }

  setMessageCount(count: number): void {
    this.messageCount = count;
    this.selectedIndex.update((index) => Math.min(Math.max(index, 0), Math.max(count - 1, 0)));
  }

  enterInsertMode(): void {
    this.commandPaletteOpen.set(false);
    this.appMode.set('INSERT');
    queueMicrotask(() => this.inputElement?.focus());
  }

  leaveInsertMode(): void {
    this.appMode.set('NORMAL');
    this.inputElement?.blur();
  }

  closeCommandPalette(): void {
    this.commandPaletteOpen.set(false);
    this.appMode.set('NORMAL');
  }

  private handleKeydown(event: KeyboardEvent): void {
    if (event.ctrlKey && event.key.toLowerCase() === 'p') {
      event.preventDefault();
      this.commandPaletteOpen.set(true);
      this.appMode.set('COMMAND');
      return;
    }

    if (event.ctrlKey && event.key.toLowerCase() === 'l') {
      event.preventDefault();
      this.clearRequested.update((value) => value + 1);
      return;
    }

    if (this.appMode() === 'COMMAND') {
      if (event.key === 'Escape') this.closeCommandPalette();
      return;
    }

    if (this.appMode() === 'INSERT') {
      if (event.key === 'Escape') {
        event.preventDefault();
        this.leaveInsertMode();
      }
      return;
    }

    if (event.key === ':' ) {
      event.preventDefault();
      this.commandPaletteOpen.set(true);
      this.appMode.set('COMMAND');
      return;
    }

    if (event.key === 'i' || event.key === '/') {
      event.preventDefault();
      this.enterInsertMode();
      return;
    }

    if (event.key === 'j' || event.key === 'ArrowDown') {
      event.preventDefault();
      this.selectedIndex.update((index) => Math.min(index + 1, Math.max(this.messageCount - 1, 0)));
    } else if (event.key === 'k' || event.key === 'ArrowUp') {
      event.preventDefault();
      this.selectedIndex.update((index) => Math.max(index - 1, 0));
    } else if (event.key === 'y') {
      event.preventDefault();
      this.copyRequested.update((value) => value + 1);
    } else if (event.key === ' ') {
      event.preventDefault();
      this.videoToggleRequested.update((value) => value + 1);
    }
  }
}
