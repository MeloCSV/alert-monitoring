import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { AlertService, Alert, AlertOverride } from '../../services/alert';
import { SearchableSelectComponent } from '../searchable-select/searchable-select';

type SeverityFilter = '' | 'warning' | 'critical' | 'principal';
type EnvironmentFilter = '' | 'dev' | 'itg' | 'pre' | 'pro';

@Component({
  selector: 'app-alert-table',
  standalone: true,
  imports: [FormsModule, SearchableSelectComponent],
  templateUrl: './alert-table.html',
  styleUrl: './alert-table.scss'
})
export class AlertTableComponent implements OnInit {
  alerts: Alert[] = [];
  overrides: AlertOverride[] = [];
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
    forkJoin({
      alerts: this.alertService.getAlerts(),
      overrides: this.alertService.getOverrides(),
    }).subscribe({
      next: ({ alerts, overrides }) => {
        this.alerts = alerts;
        this.overrides = overrides;
        this.solutionOptions = this.uniqueValues(alerts.map(a => a.solution));
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
        .filter(a => a.solution === this.solutionName)
        .map(a => a.microservice)
    );
  }

  private passesCommonFilters(alert: Alert): boolean {
    if (this.environment && !alert.environments.map(e => e.toLowerCase()).includes(this.environment)) return false;
    if (this.severity && alert.severity.toLowerCase() !== this.severity) return false;
    return true;
  }

  get defaultAlerts(): Alert[] {
    if (!this.solutionName) return [];
    const defaults = this.alerts.filter(a => a.alert_type === 'Por Defecto' && this.passesCommonFilters(a));
    const byName = new Map<string, Alert[]>();
    for (const alert of defaults) {
      const bucket = byName.get(alert.name) ?? [];
      bucket.push(alert);
      byName.set(alert.name, bucket);
    }
    const overrideStatus = this.microserviceName ? this.overrideStatusFor(this.microserviceName) : null;
    const result: Alert[] = [];
    for (const [name, bucket] of byName) {
      const representative = bucket[0];
      const status = overrideStatus?.get(name);
      result.push({
        ...representative,
        is_overridden: status === 'disabled',
        is_partial: status === 'partial',
      });
    }
    return result;
  }

  private overrideStatusFor(microservice: string): Map<string, 'disabled' | 'partial'> {
    const status = new Map<string, 'disabled' | 'partial'>();
    for (const o of this.overrides) {
      if (o.microservice !== microservice) continue;
      if (o.is_disabled) status.set(o.alert_name, 'disabled');
      else if (o.is_partial) status.set(o.alert_name, 'partial');
    }
    return status;
  }

  get adhocAlerts(): Alert[] {
    if (!this.solutionName) return [];
    return this.alerts.filter(alert => {
      if (alert.alert_type !== 'Ad-hoc') return false;
      if (alert.solution !== this.solutionName) return false;
      if (this.microserviceName && alert.microservice !== this.microserviceName) return false;
      return this.passesCommonFilters(alert);
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
