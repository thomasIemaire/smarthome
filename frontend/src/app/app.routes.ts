import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'devices',
    pathMatch: 'full',
  },
  {
    path: 'devices',
    loadComponent: () =>
      import('./pages/devices/devices-page.component').then(
        (m) => m.DevicesPageComponent
      ),
  },
  {
    path: 'weather',
    loadComponent: () =>
      import('./pages/weather/weather-page.component').then(
        (m) => m.WeatherPageComponent
      ),
  },
];
