import { Component, computed, effect, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Device } from '../../models/device.model';
import { Group } from '../../models/group.model';

@Component({
  selector: 'app-group-modal',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './group-modal.component.html',
  styleUrl: './group-modal.component.scss',
})
export class GroupModalComponent {
  group = input<Group | null>(null);
  open = input(false);
  devices = input<Device[]>([]);

  saved = output<{ id?: string; name: string; device_ids: string[] }>();
  deleted = output<string>();
  closed = output<void>();

  name = signal('');
  selectedIds = signal<Set<string>>(new Set());

  isEditing = computed(() => !!this.group());

  constructor() {
    effect(() => {
      const g = this.group();
      if (this.open()) {
        if (g) {
          this.name.set(g.name);
          this.selectedIds.set(new Set(g.device_ids));
        } else {
          this.name.set('');
          this.selectedIds.set(new Set());
        }
      }
    });
  }

  toggleDevice(id: string): void {
    this.selectedIds.update(set => {
      const next = new Set(set);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  isSelected(id: string): boolean {
    return this.selectedIds().has(id);
  }

  onSave(): void {
    const g = this.group();
    this.saved.emit({
      id: g?.id,
      name: this.name(),
      device_ids: Array.from(this.selectedIds()),
    });
  }

  onDelete(): void {
    const g = this.group();
    if (g) {
      this.deleted.emit(g.id);
    }
  }

  onClose(): void {
    this.closed.emit();
  }

  onOverlayClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('overlay')) {
      this.onClose();
    }
  }
}
