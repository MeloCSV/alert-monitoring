import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AlertService, Alert } from '../../services/alert';
import { SearchableSelectComponent } from '../searchable-select/searchable-select';

type SeverityFilter = '' | 'warning' | 'critical' | 'principal';
type EnvironmentFilter = '' | 'dev' | 'itg' | 'pre' | 'pro';

type AlertWithOverride = Alert & { is_overridden: boolean };

@Component({
  selector: 'app-alert-table',
  standalone: true,
  imports: [FormsModule, SearchableSelectComponent],
  templateUrl: './alert-table.html',
  styleUrl: './alert-table.scss'
})
export class AlertTableComponent implements OnInit {
  alerts: Alert[] = [];
  loading = true;
  error = false;

  solutionName = '';

  microserviceName = '';
  environment: EnvironmentFilter = '';
  severity: SeverityFilter = '';

  showOptionalFilters = false;

  solutionOptions: string[] = [];

  constructor(private alertService: AlertService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.alertService.getAlerts().subscribe({
      next: (data) => {
        this.alerts = data;
        this.solutionOptions = this.uniqueValues(
          data
            .filter(a => a.alert_type === 'Ad-hoc')
            .map(a => a.solution)
        );
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = true;
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  private uniqueValues(values: (string | null | undefined)[]): string[] {
    return Array.from(new Set(values.filter((v): v is string => !!v))).sort();
  }

  get microserviceOptions(): string[] {
    if (!this.solutionName) return [];
    return this.uniqueValues(
      this.alerts
        .filter(a => a.alert_type === 'Ad-hoc' && a.solution === this.solutionName)
        .map(a => a.microservice)
    );
  }

  private get appAdhocAlerts(): Alert[] {
    if (!this.solutionName) return [];
    return this.alerts.filter(a =>
      a.alert_type === 'Ad-hoc' && a.solution === this.solutionName
    );
  }

  private get appNamespaces(): string[] {
    if (this.microserviceName) return [this.microserviceName];
    return this.uniqueValues(this.appAdhocAlerts.map(a => a.microservice));
  }

  private namespaceMatches(pattern: string, namespace: string): boolean {
    if (!pattern || !namespace) return false;
    try {
      const re = new RegExp('^(?:' + pattern + ')$');
      return re.test(namespace);
    } catch {
      return pattern === namespace;
    }
  }

  private isExcepted(alert: Alert): boolean {
    const namespaces = this.appNamespaces;
    if (namespaces.length === 0) return false;
    return (alert.excluded_namespaces || []).some(pattern =>
      namespaces.some(ns => this.namespaceMatches(pattern, ns))
    );
  }

  private passesOptionalFilters(alert: Alert): boolean {
    if (this.environment && !alert.environments.map(e => e.toLowerCase()).includes(this.environment)) return false;
    if (this.severity && alert.severity.toLowerCase() !== this.severity) return false;
    return true;
  }

  get defaultAlerts(): AlertWithOverride[] {
    if (!this.solutionName) return [];
    return this.alerts
      .filter(a => a.alert_type === 'Por Defecto')
      .filter(a => this.passesOptionalFilters(a))
      .map(a => ({ ...a, is_overridden: this.isExcepted(a) }));
  }

  get adhocAlerts(): Alert[] {
    if (!this.solutionName) return [];
    return this.appAdhocAlerts.filter(alert => {
      if (this.microserviceName && alert.microservice !== this.microserviceName) return false;
      return this.passesOptionalFilters(alert);
    });
  }

  get hasSolutionSelected(): boolean {
    return !!this.solutionName;
  }

  onSolutionChange(value: string): void {
    this.solutionName = value;
    this.microserviceName = '';
    this.cdr.detectChanges();
  }

  toggleOptionalFilters(): void {
    this.showOptionalFilters = !this.showOptionalFilters;
  }

  clearOptionalFilters(): void {
    this.microserviceName = '';
    this.environment = '';
    this.severity = '';
  }

  environmentsLabel(alert: Alert): string {
    return alert.environments && alert.environments.length ? alert.environments.join(', ') : '-';
  }
}
