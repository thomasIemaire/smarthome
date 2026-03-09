import { Injectable, computed, inject, signal } from '@angular/core';
import { Device } from '../models/device.model';
import { RoomInfo } from '../models/room.model';
import { DeviceService } from '../services/device.service';
import { GroupService } from '../services/group.service';
import { ToastService } from '../services/toast.service';
import { GroupStore } from './group.store';
import { forkJoin } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class DeviceStore {
  private readonly deviceService = inject(DeviceService);
  private readonly groupService = inject(GroupService);
  private readonly toastService = inject(ToastService);
  private readonly groupStore = inject(GroupStore);

  private autoRefreshId: ReturnType<typeof setInterval> | null = null;

  readonly devices = signal<Device[]>([]);
  readonly loading = signal(false);
  readonly scanning = signal(false);
  readonly selectedRoom = signal('all');

  readonly filteredDevices = computed(() => {
    const room = this.selectedRoom();
    const all = this.devices();
    if (room === 'all') {
      return all;
    }
    return all.filter(d => d.room === room);
  });

  readonly rooms = computed<RoomInfo[]>(() => {
    const all = this.devices();
    const roomMap = new Map<string, { total: number; active: number }>();

    for (const device of all) {
      const room = device.room || 'Unassigned';
      const entry = roomMap.get(room) || { total: 0, active: 0 };
      entry.total++;
      if (device.state) {
        entry.active++;
      }
      roomMap.set(room, entry);
    }

    return Array.from(roomMap.entries()).map(([name, info]) => ({
      name,
      total: info.total,
      active: info.active,
    }));
  });

  readonly activeCount = computed(() =>
    this.devices().filter(d => d.state).length
  );

  readonly inactiveCount = computed(() =>
    this.devices().filter(d => !d.state).length
  );

  readonly statusText = computed(() => {
    const total = this.devices().length;
    const active = this.activeCount();
    return `${active} of ${total} devices active`;
  });

  loadDevices(): void {
    this.loading.set(true);

    forkJoin({
      devices: this.deviceService.getAll(),
      groups: this.groupService.getAll(),
    }).subscribe({
      next: ({ devices, groups }) => {
        this.devices.set(devices);
        this.groupStore.groups.set(groups);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.toastService.show('Failed to load devices', 'error');
      },
    });
  }

  toggleDevice(id: string): void {
    const previous = this.devices();
    this.devices.update(list =>
      list.map(d => (d.id === id ? { ...d, state: !d.state } : d))
    );

    this.deviceService.toggle(id).subscribe({
      next: () => {
        this.toastService.show('Device toggled', 'success');
      },
      error: () => {
        this.devices.set(previous);
        this.toastService.show('Failed to toggle device', 'error');
      },
    });
  }

  updateDevice(id: string, data: { name?: string; room?: string; type?: string }): void {
    this.deviceService.update(id, data).subscribe({
      next: () => {
        this.loadDevices();
        this.toastService.show('Device updated', 'success');
      },
      error: () => {
        this.toastService.show('Failed to update device', 'error');
      },
    });
  }

  allOn(): void {
    this.deviceService.allOn().subscribe({
      next: () => {
        this.loadDevices();
        this.toastService.show('All devices turned on', 'success');
      },
      error: () => {
        this.toastService.show('Failed to turn all on', 'error');
      },
    });
  }

  allOff(): void {
    this.deviceService.allOff().subscribe({
      next: () => {
        this.loadDevices();
        this.toastService.show('All devices turned off', 'success');
      },
      error: () => {
        this.toastService.show('Failed to turn all off', 'error');
      },
    });
  }

  discover(): void {
    this.scanning.set(true);
    this.deviceService.discover().subscribe({
      next: (res) => {
        this.scanning.set(false);
        this.loadDevices();
        this.toastService.show(
          `Discovered ${res.discovered} device(s)`,
          'success'
        );
      },
      error: () => {
        this.scanning.set(false);
        this.toastService.show('Discovery failed', 'error');
      },
    });
  }

  setRoom(room: string): void {
    this.selectedRoom.set(room);
  }

  startAutoRefresh(): void {
    this.stopAutoRefresh();
    this.autoRefreshId = setInterval(() => {
      this.loadDevices();
    }, 10000);
  }

  stopAutoRefresh(): void {
    if (this.autoRefreshId !== null) {
      clearInterval(this.autoRefreshId);
      this.autoRefreshId = null;
    }
  }
}
