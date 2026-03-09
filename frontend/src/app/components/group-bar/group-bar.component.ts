import { Component, inject, signal } from '@angular/core';
import { DeviceStore } from '../../stores/device.store';
import { GroupStore } from '../../stores/group.store';
import { Group } from '../../models/group.model';
import { GroupModalComponent } from '../group-modal/group-modal.component';

@Component({
  selector: 'app-group-bar',
  standalone: true,
  imports: [GroupModalComponent],
  templateUrl: './group-bar.component.html',
  styleUrl: './group-bar.component.scss',
})
export class GroupBarComponent {
  readonly deviceStore = inject(DeviceStore);
  readonly groupStore = inject(GroupStore);

  modalOpen = signal(false);
  editingGroup = signal<Group | null>(null);

  onChipClick(group: Group): void {
    this.groupStore.toggleGroup(group.id);
  }

  onEditClick(event: MouseEvent, group: Group): void {
    event.stopPropagation();
    this.editingGroup.set(group);
    this.modalOpen.set(true);
  }

  onAddClick(): void {
    this.editingGroup.set(null);
    this.modalOpen.set(true);
  }

  onModalSaved(data: { id?: string; name: string; device_ids: string[] }): void {
    if (data.id) {
      this.groupStore.updateGroup(data.id, data.name, data.device_ids);
    } else {
      this.groupStore.createGroup(data.name, data.device_ids);
    }
    this.modalOpen.set(false);
  }

  onModalDeleted(id: string): void {
    this.groupStore.deleteGroup(id);
    this.modalOpen.set(false);
  }

  onModalClosed(): void {
    this.modalOpen.set(false);
  }
}
