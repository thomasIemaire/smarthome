import { Component, inject } from '@angular/core';
import { DeviceStore } from '../../stores/device.store';

@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss',
})
export class HeaderComponent {
  readonly store = inject(DeviceStore);
}
