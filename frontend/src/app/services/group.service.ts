import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Group } from '../models/group.model';
import { GroupActionResponse, SimpleResponse } from '../models/api-response.model';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class GroupService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getAll(): Observable<Group[]> {
    return this.http.get<Group[]>(`${this.baseUrl}/groups`);
  }

  create(name: string, deviceIds: string[]): Observable<GroupActionResponse> {
    return this.http.post<GroupActionResponse>(`${this.baseUrl}/groups`, {
      name,
      device_ids: deviceIds,
    });
  }

  update(id: string, name: string, deviceIds: string[]): Observable<any> {
    return this.http.put(`${this.baseUrl}/groups/${id}`, {
      name,
      device_ids: deviceIds,
    });
  }

  toggle(id: string): Observable<GroupActionResponse> {
    return this.http.post<GroupActionResponse>(`${this.baseUrl}/groups/${id}/toggle`, {});
  }

  delete(id: string): Observable<SimpleResponse> {
    return this.http.delete<SimpleResponse>(`${this.baseUrl}/groups/${id}`);
  }
}
