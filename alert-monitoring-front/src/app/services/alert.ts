import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface CatalogApp {
  object_id: string;
  object_key: string;
  name: string;
  csw_code: string | null;
  platform: string | null;
}

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
  prometheus_name: string | null;
  is_disabled?: boolean;
  is_partial?: boolean;
  chips?: string[];
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
  source?: string | null;
}


export interface AlertApi {
  rule_id: string;
  name: string;
  enabled: boolean;
  tags: string[];
  severity: string | null;
  notification_channel: string | null;
  apis_alertadas: string[];
  message: string | null;
}

export interface DefaultAlertApiView {
  raw_name: string;
  name: string;
  description: string | null;
  severity: string | null;
  notification_channel: string | null;
  environments: string[];
  is_disabled: boolean;
  is_partial: boolean;
  chips: string[];
}

export interface ApiSolutionView {
  app: string;
  default_alerts: DefaultAlertApiView[];
  adhoc_alerts: AlertApi[];
  api_microservice_map: Record<string, string>;
  channels: string[];
}

export interface DefaultAlertView {
  raw_name: string;
  name: string;
  description: string | null;
  severity: string | null;
  notification_channel: string | null;
  environments: string[];
  is_disabled: boolean;
  is_partial: boolean;
  chips: string[];
}

export interface SolutionView {
  solution: string;
  default_alerts: DefaultAlertView[];
  adhoc_alerts: Alert[];
  channels: string[];
}

@Injectable({ providedIn: 'root' })
export class AlertService {
  private readonly apiUrl = 'http://localhost:8080/alerts';
  private readonly catalogUrl = 'http://localhost:8080/catalog';
  private readonly kibanaRulesUrl = 'http://localhost:8080/kibana-rules';

  constructor(private http: HttpClient) {}

  getCatalogApps(): Observable<CatalogApp[]> {
    return this.http.get<CatalogApp[]>(this.catalogUrl);
  }

  getSolutionView(solution: string): Observable<SolutionView> {
    const params = new HttpParams().set('solution', solution);
    return this.http.get<SolutionView>(`${this.apiUrl}/view`, { params });
  }

  getBlackouts(solution?: string): Observable<Blackout[]> {
    const params = solution ? new HttpParams().set('solution', solution) : undefined;
    return this.http.get<Blackout[]>(`${this.apiUrl}/blackouts`, { params });
  }

  getApiSolutionView(app: string): Observable<ApiSolutionView> {
    const params = new HttpParams().set('app', app);
    return this.http.get<ApiSolutionView>(`${this.apiUrl}/api-view`, { params });
  }
}
