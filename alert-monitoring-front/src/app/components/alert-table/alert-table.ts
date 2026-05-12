import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AlertService, Alert } from '../../services/alert';
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
        this.solutionOptions = this.uniqueValues(data.map(a => a.solution));
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
    const targetMicroservices = this.microserviceName
      ? [this.microserviceName]
      : this.microserviceOptions;
    const solutionAdhoc = this.alerts.filter(a => {
      if (a.alert_type !== 'Ad-hoc' || a.solution !== this.solutionName) return false;
      if (this.microserviceName && a.microservice !== this.microserviceName) return false;
      return true;
    });
    const result: Alert[] = [];
    for (const [, bucket] of byName) {
      const representative = bucket[0];
      const defaultBaseName = this.alertBaseName(representative.name);
      const excludedByNamespace = targetMicroservices.length > 0
        && !targetMicroservices.some(ms => bucket.some(a => this.ruleAppliesToMicroservice(a, ms)));
      const overriddenByAdhoc = solutionAdhoc.some(a => this.alertBaseName(a.name) === defaultBaseName);
      result.push({ ...representative, is_overridden: excludedByNamespace || overriddenByAdhoc });
    }
    return result;
  }

  private alertBaseName(name: string): string {
    const idx = name.indexOf('_');
    return idx >= 0 ? name.slice(idx + 1) : name;
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

  private ruleAppliesToMicroservice(alert: Alert, microservice: string): boolean {
    const hasInclude = !!alert.included_namespaces;
    const hasExclude = !!alert.excluded_namespaces;
    if (!hasInclude && !hasExclude) return true;
    if (hasInclude && !this.matchesPrometheusPattern(microservice, alert.included_namespaces)) return false;
    if (hasExclude && this.matchesPrometheusPattern(microservice, alert.excluded_namespaces)) return false;
    return true;
  }

  private matchesPrometheusPattern(value: string, pattern: string | null): boolean {
    if (!pattern) return false;
    try {
      return new RegExp(`^(?:${pattern})$`).test(value);
    } catch {
      return false;
    }
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
