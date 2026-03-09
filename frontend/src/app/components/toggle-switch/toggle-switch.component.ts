import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-toggle-switch',
  standalone: true,
  templateUrl: './toggle-switch.component.html',
  styleUrl: './toggle-switch.component.scss',
})
export class ToggleSwitchComponent {
  checked = input(false);
  accentType = input<'plug' | 'light'>('plug');
  changed = output<void>();

  onToggle(): void {
    this.changed.emit();
  }
}
