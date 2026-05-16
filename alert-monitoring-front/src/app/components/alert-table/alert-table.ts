import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { AlertService, Alert, AlertOverride, Blackout } from '../../services/alert';
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
  blackouts: Blackout[] = [];
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
      blackouts: this.alertService.getBlackouts(),
    }).subscribe({
      next: ({ alerts, overrides, blackouts }) => {
        this.alerts = alerts;
        this.overrides = overrides;
        this.blackouts = blackouts;
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

  private matchesBlackoutValue(matcherValue: string, isRegex: boolean, isEqual: boolean, candidate: string): boolean {
    let hit: boolean;
    if (isRegex) {
      try {
        hit = new RegExp(`^(?:${matcherValue})$`).test(candidate);
      } catch {
        return false;
      }
    } else {
      hit = matcherValue === candidate;
    }
    return isEqual ? hit : !hit;
  }

  private findBlackoutForAlert(alert: Alert): Blackout | null {
    for (const blackout of this.blackouts) {
      const nameMatchers = blackout.matchers.filter(m => m.name === 'alertname');
      if (nameMatchers.length === 0) continue;
      const nameOk = nameMatchers.every(m =>
        this.matchesBlackoutValue(m.value, m.is_regex, m.is_equal, alert.name)
      );
      if (!nameOk) continue;
      const severityMatchers = blackout.matchers.filter(m => m.name === 'severity');
      const severityOk = severityMatchers.every(m =>
        this.matchesBlackoutValue(m.value, m.is_regex, m.is_equal, (alert.severity || '').toLowerCase())
      );
      if (!severityOk) continue;
      const envMatchers = blackout.matchers.filter(m => m.name === 'environment' || m.name === 'environments');
      const envOk = envMatchers.every(m =>
        alert.environments.some(e => this.matchesBlackoutValue(m.value, m.is_regex, m.is_equal, e.toLowerCase()))
      );
      if (!envOk) continue;
      return blackout;
    }
    return null;
  }

  formatBlackoutDate(isoDate: string | null | undefined): string {
    if (!isoDate) return '';
    const d = new Date(isoDate);
    return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
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
    const overrideStatus = this.overrideStatusFor(this.solutionName);
    const result: Alert[] = [];
    for (const [name, bucket] of byName) {
      const representative = bucket[0];
      const status = overrideStatus.get(name);
      const blackout = this.findBlackoutForAlert(representative);
      result.push({
        ...representative,
        is_overridden: status === 'disabled',
        is_partial: status === 'partial',
        is_blackout: blackout !== null,
        blackout,
      });
    }
    return result;
  }

  private overrideStatusFor(solution: string): Map<string, 'disabled' | 'partial'> {
    const status = new Map<string, 'disabled' | 'partial'>();
    for (const o of this.overrides) {
      if (o.solution !== solution) continue;
      if (o.is_disabled) status.set(o.alert_name, 'disabled');
      else if (o.is_partial) status.set(o.alert_name, 'partial');
    }
    return status;
  }

  get adhocAlerts(): Alert[] {
    if (!this.solutionName) return [];
    return this.alerts
      .filter(alert => {
        if (alert.alert_type !== 'Ad-hoc') return false;
        if (alert.solution !== this.solutionName) return false;
        if (this.microserviceName && alert.microservice !== this.microserviceName) return false;
        return this.passesCommonFilters(alert);
      })
      .map(alert => {
        const blackout = this.findBlackoutForAlert(alert);
        return { ...alert, is_blackout: blackout !== null, blackout };
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
