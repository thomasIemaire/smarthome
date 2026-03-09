import { Component, input, output } from '@angular/core';
import { Device } from '../../models/device.model';
import { ToggleSwitchComponent } from '../toggle-switch/toggle-switch.component';

@Component({
  selector: 'app-device-card',
  standalone: true,
  imports: [ToggleSwitchComponent],
  templateUrl: './device-card.component.html',
  styleUrl: './device-card.component.scss',
})
export class DeviceCardComponent {
  device = input.required<Device>();
  toggled = output<string>();
  editClicked = output<string>();

  get icon(): string {
    return this.device().type === 'plug' ? '\uD83D\uDD0C' : '\uD83D\uDCA1';
  }

  get statusText(): string {
    return this.device().state ? 'On' : 'Off';
  }

  onToggle(): void {
    this.toggled.emit(this.device().id);
  }

  onEdit(event: MouseEvent): void {
    event.stopPropagation();
    this.editClicked.emit(this.device().id);
  }
}
