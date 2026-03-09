import { Component, signal, computed, afterNextRender, inject } from '@angular/core';
import {
  WeatherService,
  WeatherData,
  GeoLocation,
} from '../../services/weather.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-weather-page',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './weather-page.component.html',
  styleUrl: './weather-page.component.scss',
})
export class WeatherPageComponent {
  private readonly weatherService = inject(WeatherService);

  readonly weather = signal<WeatherData | null>(null);
  readonly loading = signal(true);
  readonly locationName = signal('Chargement...');
  readonly searchQuery = signal('');
  readonly searchResults = signal<GeoLocation[]>([]);
  readonly showSearch = signal(false);

  readonly description = computed(() => {
    const w = this.weather();
    if (!w) return '';
    return this.weatherService.getDescription(w.current.weatherCode);
  });

  readonly weatherIcon = computed(() => {
    const w = this.weather();
    if (!w) return 'cloud';
    return this.weatherService.getIcon(w.current.weatherCode);
  });

  constructor() {
    afterNextRender(() => this.initLocation());
  }

  async initLocation(): Promise<void> {
    try {
      const pos = await this.weatherService.getCurrentPosition();
      this.loadWeather(
        pos.coords.latitude,
        pos.coords.longitude,
        'Ma position'
      );
    } catch {
      this.loadWeather(48.8566, 2.3522, 'Paris, France');
    }
  }

  loadWeather(lat: number, lon: number, name: string): void {
    this.loading.set(true);
    this.locationName.set(name);
    this.weatherService.getWeather(lat, lon).subscribe({
      next: (data) => {
        this.weather.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  onSearch(): void {
    const q = this.searchQuery();
    if (q.length < 2) {
      this.searchResults.set([]);
      return;
    }
    this.weatherService.searchCity(q).subscribe({
      next: (results) => this.searchResults.set(results),
    });
  }

  selectCity(loc: GeoLocation): void {
    this.loadWeather(loc.latitude, loc.longitude, loc.name);
    this.showSearch.set(false);
    this.searchQuery.set('');
    this.searchResults.set([]);
  }

  toggleSearch(): void {
    this.showSearch.update((v) => !v);
    if (!this.showSearch()) {
      this.searchQuery.set('');
      this.searchResults.set([]);
    }
  }

  formatHour(time: string): string {
    return new Date(time).toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  getIconForCode(code: number): string {
    return this.weatherService.getIcon(code);
  }

  getDescForCode(code: number): string {
    return this.weatherService.getDescription(code);
  }
}
