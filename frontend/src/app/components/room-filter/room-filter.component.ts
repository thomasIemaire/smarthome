import { Component, input, output } from '@angular/core';
import { RoomInfo } from '../../models/room.model';

@Component({
  selector: 'app-room-filter',
  standalone: true,
  templateUrl: './room-filter.component.html',
  styleUrl: './room-filter.component.scss',
})
export class RoomFilterComponent {
  rooms = input<RoomInfo[]>([]);
  selectedRoom = input('all');
  totalCount = input(0);
  roomSelected = output<string>();

  selectRoom(room: string): void {
    this.roomSelected.emit(room);
  }
}
