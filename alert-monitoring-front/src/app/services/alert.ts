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
  is_overridden: boolean;
  excluded_namespaces: string | null;
  included_namespaces: string | null;
}

export interface AlertOverride {
  alert_name: string;
  microservice: string;
  is_disabled: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AlertService {
  private apiUrl = 'http://localhost:8080/alerts';

  constructor(private http: HttpClient) {}

  getAlerts(): Observable<Alert[]> {
    return this.http.get<Alert[]>(this.apiUrl);
  }

  getOverrides(microservice?: string): Observable<AlertOverride[]> {
    const url = microservice
      ? `${this.apiUrl}/overrides?microservice=${encodeURIComponent(microservice)}`
      : `${this.apiUrl}/overrides`;
    return this.http.get<AlertOverride[]>(url);
  }
}