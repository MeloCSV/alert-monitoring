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
  confidence_level: number;
  alert_type: 'Por Defecto' | 'Ad-hoc';
  is_overridden: boolean;
  excluded_namespaces: string[];
  target_namespaces: string[];
  category: string | null;
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
}