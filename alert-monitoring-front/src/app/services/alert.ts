import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Alert {
  name: string;
  description: string;
  source_tool: string | null;
  severity: string;
  condition: string;
  environments: string[];
  microservice: string | null;
  solution: string | null;
  notification_channel: string | null;
  alert_type: 'Por Defecto' | 'Ad-hoc';
  cluster: string | null;
  is_overridden?: boolean;
  is_partial?: boolean;
  is_blackout?: boolean;
  is_partial_blackout?: boolean;
  blackout_environments?: string[];
  blackout?: Blackout | null;
  chips?: string[];
}

export interface AlertOverride {
  alert_name: string;
  solution: string;
  is_disabled: boolean;
  is_partial: boolean;
  excluded_items: string[];
}

export interface BlackoutMatcher {
  name: string;
  value: string;
  is_regex: boolean;
  is_equal: boolean;
}

export interface Blackout {
  id: string;
  matchers: BlackoutMatcher[];
  starts_at?: string | null;
  ends_at?: string | null;
  created_by?: string | null;
  comment?: string | null;
}

@Injectable({ providedIn: 'root' })
export class AlertService {
  private readonly apiUrl = 'http://localhost:8080/alerts';

  constructor(private http: HttpClient) {}

  getAlerts(): Observable<Alert[]> {
    return this.http.get<Alert[]>(this.apiUrl);
  }

  getOverrides(): Observable<AlertOverride[]> {
    return this.http.get<AlertOverride[]>(`${this.apiUrl}/overrides`);
  }

  getBlackouts(): Observable<Blackout[]> {
    return this.http.get<Blackout[]>(`${this.apiUrl}/blackouts`);
  }
}
