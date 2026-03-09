import { Injectable, signal } from '@angular/core';

export interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error' | '';
  visible: boolean;
}

@Injectable({ providedIn: 'root' })
export class ToastService {
  readonly toasts = signal<Toast[]>([]);

  private nextId = 0;

  show(message: string, type: 'success' | 'error' | '' = ''): void {
    const id = this.nextId++;
    const toast: Toast = { id, message, type, visible: false };

    this.toasts.update(list => [...list, toast]);

    requestAnimationFrame(() => {
      this.toasts.update(list =>
        list.map(t => (t.id === id ? { ...t, visible: true } : t))
      );
    });

    setTimeout(() => {
      this.remove(id);
    }, 3000);
  }

  remove(id: number): void {
    this.toasts.update(list => list.filter(t => t.id !== id));
  }
}
