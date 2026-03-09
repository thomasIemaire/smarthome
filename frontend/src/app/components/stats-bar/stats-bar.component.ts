import { Component, input } from '@angular/core';

@Component({
  selector: 'app-stats-bar',
  standalone: true,
  templateUrl: './stats-bar.component.html',
  styleUrl: './stats-bar.component.scss',
})
export class StatsBarComponent {
  activeCount = input(0);
  inactiveCount = input(0);
}
