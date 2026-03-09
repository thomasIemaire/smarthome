import { Component, effect, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Device } from '../../models/device.model';

@Component({
  selector: 'app-device-edit-modal',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './device-edit-modal.component.html',
  styleUrl: './device-edit-modal.component.scss',
})
export class DeviceEditModalComponent {
  device = input<Device | null>(null);
  open = input(false);
  existingRooms = input<string[]>([]);

  saved = output<{ id: string; name: string; room: string; type: string }>();
  closed = output<void>();

  name = signal('');
  room = signal('');
  type = signal<string>('plug');

  constructor() {
    effect(() => {
      const d = this.device();
      if (d && this.open()) {
        this.name.set(d.name);
        this.room.set(d.room);
        this.type.set(d.type);
      }
    });
  }

  onSave(): void {
    const d = this.device();
    if (!d) return;
    this.saved.emit({
      id: d.id,
      name: this.name(),
      room: this.room(),
      type: this.type(),
    });
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
