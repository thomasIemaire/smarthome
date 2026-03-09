import { Injectable, Injector, inject, signal } from '@angular/core';
import { Group } from '../models/group.model';
import { GroupService } from '../services/group.service';
import { ToastService } from '../services/toast.service';

@Injectable({ providedIn: 'root' })
export class GroupStore {
  private readonly groupService = inject(GroupService);
  private readonly toastService = inject(ToastService);
  private readonly injector = inject(Injector);

  readonly groups = signal<Group[]>([]);

  /**
   * Lazily resolves DeviceStore to break the circular injection chain.
   * DeviceStore injects GroupStore at construction, so GroupStore cannot
   * use inject(DeviceStore). We resolve it from the injector on first use.
   * The import is placed inside the method to avoid a circular module
   * reference at the top level.
   */
  private _deviceStore: { loadDevices(): void } | null = null;

  private async resolveDeviceStore(): Promise<{ loadDevices(): void }> {
    if (!this._deviceStore) {
      const { DeviceStore } = await import('./device.store');
      this._deviceStore = this.injector.get(DeviceStore);
    }
    return this._deviceStore;
  }

  private reloadDevices(): void {
    this.resolveDeviceStore().then(store => store.loadDevices());
  }

  loadGroups(): void {
    this.groupService.getAll().subscribe({
      next: (groups) => this.groups.set(groups),
      error: () => this.toastService.show('Failed to load groups', 'error'),
    });
  }

  toggleGroup(id: string): void {
    this.groupService.toggle(id).subscribe({
      next: () => {
        this.reloadDevices();
        this.toastService.show('Group toggled', 'success');
      },
      error: () => this.toastService.show('Failed to toggle group', 'error'),
    });
  }

  createGroup(name: string, deviceIds: string[]): void {
    this.groupService.create(name, deviceIds).subscribe({
      next: () => {
        this.reloadDevices();
        this.toastService.show('Group created', 'success');
      },
      error: () => this.toastService.show('Failed to create group', 'error'),
    });
  }

  updateGroup(id: string, name: string, deviceIds: string[]): void {
    this.groupService.update(id, name, deviceIds).subscribe({
      next: () => {
        this.reloadDevices();
        this.toastService.show('Group updated', 'success');
      },
      error: () => this.toastService.show('Failed to update group', 'error'),
    });
  }

  deleteGroup(id: string): void {
    this.groupService.delete(id).subscribe({
      next: () => {
        this.reloadDevices();
        this.toastService.show('Group deleted', 'success');
      },
      error: () => this.toastService.show('Failed to delete group', 'error'),
    });
  }
}
