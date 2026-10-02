import { Injectable } from '@angular/core';

export interface CommandResult {
  message?: string;
  engine?: string;
  model?: string;
}

@Injectable({ providedIn: 'root' })
export class CommandService {
  execute(rawCommand: string): CommandResult {
    const [command, ...args] = rawCommand.trim().replace(/^:/, '').split(/\s+/);
    switch (command?.toLowerCase()) {
      case 'clear': return { message: 'Terminal cleared' };
      case 'config': return { message: 'Configuration panel is ready' };
      case 'engine': return { engine: args.join(' ') || 'local' };
      case 'model': return { model: args.join(' ') || 'qwen3-8b' };
      default: return { message: command ? `Unknown command: ${command}` : undefined };
    }
  }
}
