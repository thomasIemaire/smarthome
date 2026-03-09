export interface Device {
  id: string;
  name: string;
  room: string;
  type: 'plug' | 'light';
  protocol: 'shelly' | 'meross' | 'simulation';
  ip: string;
  state: boolean;
  icon: 'plug' | 'bulb';
  gen?: number;
  model?: string;
  meross_uuid?: string;
}
