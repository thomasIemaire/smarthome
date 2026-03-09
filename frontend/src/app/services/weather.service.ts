import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';

export interface CurrentWeather {
  temperature: number;
  apparentTemperature: number;
  humidity: number;
  windSpeed: number;
  weatherCode: number;
  isDay: boolean;
}

export interface HourlyForecast {
  time: string;
  temperature: number;
  weatherCode: number;
}

export interface DailyForecast {
  date: string;
  dayName: string;
  weatherCode: number;
  tempMax: number;
  tempMin: number;
}

export interface WeatherData {
  current: CurrentWeather;
  hourly: HourlyForecast[];
  daily: DailyForecast[];
}

export interface GeoLocation {
  latitude: number;
  longitude: number;
  name: string;
}

const WEATHER_DESCRIPTIONS: Record<number, string> = {
  0: 'Ciel dégagé',
  1: 'Principalement dégagé',
  2: 'Partiellement nuageux',
  3: 'Couvert',
  45: 'Brouillard',
  48: 'Brouillard givrant',
  51: 'Bruine légère',
  53: 'Bruine modérée',
  55: 'Bruine dense',
  61: 'Pluie légère',
  63: 'Pluie modérée',
  65: 'Pluie forte',
  66: 'Pluie verglaçante légère',
  67: 'Pluie verglaçante forte',
  71: 'Neige légère',
  73: 'Neige modérée',
  75: 'Neige forte',
  77: 'Grains de neige',
  80: 'Averses légères',
  81: 'Averses modérées',
  82: 'Averses violentes',
  85: 'Averses de neige légères',
  86: 'Averses de neige fortes',
  95: 'Orage',
  96: 'Orage avec grêle légère',
  99: 'Orage avec grêle forte',
};

const WEATHER_ICONS: Record<number, string> = {
  0: 'sun',
  1: 'sun',
  2: 'cloud-sun',
  3: 'cloud',
  45: 'fog',
  48: 'fog',
  51: 'drizzle',
  53: 'drizzle',
  55: 'drizzle',
  61: 'rain',
  63: 'rain',
  65: 'rain-heavy',
  66: 'rain',
  67: 'rain-heavy',
  71: 'snow',
  73: 'snow',
  75: 'snow',
  77: 'snow',
  80: 'rain',
  81: 'rain',
  82: 'rain-heavy',
  85: 'snow',
  86: 'snow',
  95: 'storm',
  96: 'storm',
  99: 'storm',
};

@Injectable({ providedIn: 'root' })
export class WeatherService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'https://api.open-meteo.com/v1';
  private readonly geoUrl = 'https://geocoding-api.open-meteo.com/v1';

  getWeather(lat: number, lon: number): Observable<WeatherData> {
    const params = [
      `latitude=${lat}`,
      `longitude=${lon}`,
      'current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,is_day,wind_speed_10m',
      'hourly=temperature_2m,weather_code',
      'daily=weather_code,temperature_2m_max,temperature_2m_min',
      'timezone=auto',
      'forecast_days=7',
    ].join('&');

    return this.http
      .get<any>(`${this.baseUrl}/forecast?${params}`)
      .pipe(map((res) => this.mapResponse(res)));
  }

  searchCity(query: string): Observable<GeoLocation[]> {
    return this.http
      .get<any>(`${this.geoUrl}/search?name=${encodeURIComponent(query)}&count=5&language=fr`)
      .pipe(
        map((res) =>
          (res.results || []).map((r: any) => ({
            latitude: r.latitude,
            longitude: r.longitude,
            name: `${r.name}, ${r.country}`,
          }))
        )
      );
  }

  reverseGeocode(lat: number, lon: number): Observable<string> {
    return this.http
      .get<any>(`${this.geoUrl}/search?name=&count=1&language=fr`)
      .pipe(map(() => `${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E`));
  }

  getDescription(code: number): string {
    return WEATHER_DESCRIPTIONS[code] || 'Inconnu';
  }

  getIcon(code: number): string {
    return WEATHER_ICONS[code] || 'cloud';
  }

  getCurrentPosition(): Promise<GeolocationPosition> {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        timeout: 5000,
        enableHighAccuracy: false,
      });
    });
  }

  private mapResponse(res: any): WeatherData {
    const now = new Date();
    const currentHourIndex = res.hourly.time.findIndex(
      (t: string) => new Date(t) >= now
    );

    const hourly: HourlyForecast[] = res.hourly.time
      .slice(currentHourIndex, currentHourIndex + 24)
      .map((time: string, i: number) => ({
        time,
        temperature: Math.round(
          res.hourly.temperature_2m[currentHourIndex + i]
        ),
        weatherCode: res.hourly.weather_code[currentHourIndex + i],
      }));

    const dayNames = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];
    const daily: DailyForecast[] = res.daily.time.map(
      (date: string, i: number) => ({
        date,
        dayName: i === 0 ? "Aujourd'hui" : dayNames[new Date(date).getDay()],
        weatherCode: res.daily.weather_code[i],
        tempMax: Math.round(res.daily.temperature_2m_max[i]),
        tempMin: Math.round(res.daily.temperature_2m_min[i]),
      })
    );

    return {
      current: {
        temperature: Math.round(res.current.temperature_2m),
        apparentTemperature: Math.round(res.current.apparent_temperature),
        humidity: res.current.relative_humidity_2m,
        windSpeed: Math.round(res.current.wind_speed_10m),
        weatherCode: res.current.weather_code,
        isDay: res.current.is_day === 1,
      },
      hourly,
      daily,
    };
  }
}
