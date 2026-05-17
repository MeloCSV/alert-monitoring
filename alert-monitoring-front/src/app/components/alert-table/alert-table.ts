import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { AlertService, Alert, AlertOverride, Blackout } from '../../services/alert';
import { SearchableSelectComponent } from '../searchable-select/searchable-select';

type SeverityFilter = '' | 'warning' | 'critical' | 'principal';
type EnvironmentFilter = '' | 'dev' | 'itg' | 'pre' | 'pro';

interface OverrideStatus {
  state: 'disabled' | 'partial' | 'active';
  excluded: string[];
}

const NAMESPACE_KEYS = ['namespace', 'exported_namespace', 'backend_target_name', 'backend_name'];
const JOB_KEYS = ['job_name', 'deployment', 'horizontalpodautoscaler', 'cronjob'];

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
    const labelGetters: Record<string, () => string | string[]> = {
      alertname:    () => alert.name,
      severity:     () => (alert.severity || '').toLowerCase(),
      environment:  () => alert.environments.map(e => e.toLowerCase()),
      environments: () => alert.environments.map(e => e.toLowerCase()),
      solucion:     () => (alert.solution || '').toLowerCase(),
      solution:     () => (alert.solution || '').toLowerCase(),
      namespace:    () => (alert.microservice || '').toLowerCase(),
    };

    for (const blackout of this.blackouts) {
      const evaluatable = blackout.matchers.filter(m => m.name in labelGetters);
      if (evaluatable.length === 0) continue;

      const allMatch = evaluatable.every(m => {
        const val = labelGetters[m.name]();
        if (Array.isArray(val)) {
          return val.some(v => this.matchesBlackoutValue(m.value, m.is_regex, m.is_equal, v));
        }
        return this.matchesBlackoutValue(m.value, m.is_regex, m.is_equal, val);
      });

      if (allMatch) return blackout;
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
      const status = overrideStatus.get(name) ?? { state: 'active', excluded: [] };
      const blackout = this.findBlackoutForAlert(representative);
      result.push({
        ...representative,
        is_overridden: status.state === 'disabled',
        is_partial: status.state === 'partial',
        is_blackout: blackout !== null,
        blackout,
        chips: status.excluded,
      });
    }
    return result;
  }

  private overrideStatusFor(solution: string): Map<string, OverrideStatus> {
    const status = new Map<string, OverrideStatus>();
    for (const o of this.overrides) {
      if (o.solution !== solution) continue;
      const excluded = o.excluded_items ?? [];
      if (o.is_disabled) status.set(o.alert_name, { state: 'disabled', excluded: [] });
      else if (o.is_partial) status.set(o.alert_name, { state: 'partial', excluded });
      else if (excluded.length) status.set(o.alert_name, { state: 'active', excluded });
    }
    return status;
  }

  get adhocAlerts(): Alert[] {
    if (!this.solutionName) return [];
    return this.alerts
      .filter(alert => {
        if (alert.alert_type !== 'Ad-hoc') return false;
        if (alert.solution !== this.solutionName) return false;
        return this.passesCommonFilters(alert);
      })
      .map(alert => {
        const blackout = this.findBlackoutForAlert(alert);
        return {
          ...alert,
          is_blackout: blackout !== null,
          blackout,
          chips: this.adhocChips(alert),
        };
      });
  }

  private adhocChips(alert: Alert): string[] {
    return this.extractIncludes(alert.condition);
  }

  private extractIncludes(expr: string | null | undefined): string[] {
    if (!expr) return [];
    const out: string[] = [];
    const keys = [...JOB_KEYS, ...NAMESPACE_KEYS];
    for (const key of keys) {
      const regex = new RegExp(`${key}\\s*=~?\\s*"([^"]+)"`, 'g');
      let match: RegExpExecArray | null;
      while ((match = regex.exec(expr)) !== null) {
        for (const raw of match[1].split('|')) {
          const cleaned = this.cleanAlternative(raw);
          if (cleaned && !out.includes(cleaned)) out.push(cleaned);
        }
      }
    }
    return out;
  }

  private cleanAlternative(value: string): string {
    let v = value.trim();
    v = v.replace(/^\^/, '').replace(/\$$/, '');
    for (const suf of ['.*', '.+']) {
      if (v.endsWith(suf)) v = v.slice(0, -suf.length);
    }
    return v.replace(/-$/, '').trim();
  }

  get hasSolutionSelected(): boolean {
    return !!this.solutionName;
  }

  onSolutionChange(value: string): void {
    this.solutionName = value;
    this.cdr.detectChanges();
  }

  toggleOptionalFilters(): void {
    this.showOptionalFilters = !this.showOptionalFilters;
  }

  clearOptionalFilters(): void {
    this.environment = '';
    this.severity = '';
  }

  environmentsLabel(alert: Alert): string {
    return alert.environments && alert.environments.length ? alert.environments.join(', ') : '-';
  }
}
