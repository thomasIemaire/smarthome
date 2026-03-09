import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Device } from '../models/device.model';
import { ToggleResponse, DiscoverResponse, SimpleResponse } from '../models/api-response.model';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class DeviceService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getAll(): Observable<Device[]> {
    return this.http.get<Device[]>(`${this.baseUrl}/devices`);
  }

  toggle(id: string): Observable<ToggleResponse> {
    return this.http.post<ToggleResponse>(`${this.baseUrl}/devices/${id}/toggle`, {});
  }

  setState(id: string, state: boolean): Observable<ToggleResponse> {
    return this.http.post<ToggleResponse>(`${this.baseUrl}/devices/${id}/state`, { state });
  }

  update(id: string, data: { name?: string; room?: string; type?: string }): Observable<any> {
    return this.http.put(`${this.baseUrl}/devices/${id}`, data);
  }

  discover(): Observable<DiscoverResponse> {
    return this.http.post<DiscoverResponse>(`${this.baseUrl}/discover`, {});
  }

  allOn(): Observable<SimpleResponse> {
    return this.http.post<SimpleResponse>(`${this.baseUrl}/all/on`, {});
  }

  allOff(): Observable<SimpleResponse> {
    return this.http.post<SimpleResponse>(`${this.baseUrl}/all/off`, {});
  }
}
