import { Component, afterNextRender, inject } from '@angular/core';
import { DeviceStore } from '../../stores/device.store';
import { RoomFilterComponent } from '../../components/room-filter/room-filter.component';
import { GroupBarComponent } from '../../components/group-bar/group-bar.component';
import { StatsBarComponent } from '../../components/stats-bar/stats-bar.component';
import { DeviceGridComponent } from '../../components/device-grid/device-grid.component';

@Component({
  selector: 'app-devices-page',
  standalone: true,
  imports: [
    RoomFilterComponent,
    GroupBarComponent,
    StatsBarComponent,
    DeviceGridComponent,
  ],
  templateUrl: './devices-page.component.html',
  styleUrl: './devices-page.component.scss',
})
export class DevicesPageComponent {
  readonly store = inject(DeviceStore);

  constructor() {
    afterNextRender(() => {
      this.store.loadDevices();
      this.store.startAutoRefresh();
    });
  }

  onRoomSelected(room: string): void {
    this.store.setRoom(room);
  }
}
