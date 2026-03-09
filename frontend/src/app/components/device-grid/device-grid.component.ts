import { Component, inject, signal } from '@angular/core';
import { DeviceStore } from '../../stores/device.store';
import { Device } from '../../models/device.model';
import { DeviceCardComponent } from '../device-card/device-card.component';
import { DeviceEditModalComponent } from '../device-edit-modal/device-edit-modal.component';

@Component({
  selector: 'app-device-grid',
  standalone: true,
  imports: [DeviceCardComponent, DeviceEditModalComponent],
  templateUrl: './device-grid.component.html',
  styleUrl: './device-grid.component.scss',
})
export class DeviceGridComponent {
  readonly store = inject(DeviceStore);

  editDevice = signal<Device | null>(null);
  editModalOpen = signal(false);

  get existingRooms(): string[] {
    return this.store.rooms().map(r => r.name);
  }

  onToggled(id: string): void {
    this.store.toggleDevice(id);
  }

  onEditClicked(id: string): void {
    const device = this.store.devices().find(d => d.id === id) || null;
    this.editDevice.set(device);
    this.editModalOpen.set(true);
  }

  onModalSaved(data: { id: string; name: string; room: string; type: string }): void {
    this.store.updateDevice(data.id, {
      name: data.name,
      room: data.room,
      type: data.type,
    });
    this.editModalOpen.set(false);
  }

  onModalClosed(): void {
    this.editModalOpen.set(false);
  }
}
