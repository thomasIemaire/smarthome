import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';

interface DockApp {
  id: string;
  label: string;
  route: string;
  icon: string;
}

@Component({
  selector: 'app-dock',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './dock.component.html',
  styleUrl: './dock.component.scss',
})
export class DockComponent {
  readonly apps: DockApp[] = [
    {
      id: 'devices',
      label: 'Appareils',
      route: '/devices',
      icon: 'devices',
    },
    {
      id: 'weather',
      label: 'Météo',
      route: '/weather',
      icon: 'weather',
    },
  ];
}
