export interface ToggleResponse {
  id: string;
  name: string;
  state: boolean;
  message?: string;
}

export interface DiscoverResponse {
  discovered: number;
  devices: string[];
  message?: string;
}

export interface GroupActionResponse {
  id: string;
  name: string;
  active: boolean;
  toggled: string[];
  message?: string;
}

export interface SimpleResponse {
  message: string;
  toggled?: number;
}
