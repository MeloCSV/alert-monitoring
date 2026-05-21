import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { AlertService, Alert, AlertOverride, Blackout, CatalogApp, DefaultAlert } from '../../services/alert';
import { SearchableSelectComponent } from '../searchable-select/searchable-select';

type EnvironmentFilter = '' | 'dev' | 'itg' | 'pre' | 'pro';
type SeverityFilter = '' | 'warning' | 'principal' | 'critical';

interface OverrideStatus {
  state: 'disabled' | 'partial' | 'active';
  excluded: string[];
}

interface DefaultAlertRow {
  raw_name: string;
  name: string;
  description: string | null;
  severity: string | null;
  notification_channel: string | null;
  environments: string[];
  is_overridden: boolean;
  is_partial: boolean;
  chips: string[];
  prometheus_name: string;
}

const NAMESPACE_KEYS = ['namespace', 'exported_namespace', 'backend_target_name', 'backend_name'];
const JOB_KEYS = ['job_name', 'deployment', 'horizontalpodautoscaler', 'cronjob'];
const APP_MATCHER_FIELDS = new Set([
  'namespace', 'solucion', 'solution', 'exported_namespace',
  'backend_target_name', 'deployment', 'replicaset', 'cronjob', 'pod'
]);

@Component({
  selector: 'app-alert-table',
  standalone: true,
  imports: [FormsModule, SearchableSelectComponent],
  templateUrl: './alert-table.html',
  styleUrl: './alert-table.scss'
})
export class AlertTableComponent implements OnInit {
  alerts: Alert[] = [];
  canonicalDefaults: DefaultAlert[] = [];
  overrides: AlertOverride[] = [];
  blackouts: Blackout[] = [];
  catalogApps: CatalogApp[] = [];
  loading = true;
  error = false;

  solutionName = '';

  environment: EnvironmentFilter = '';
  channel = '';
  severity: SeverityFilter = '';

  showOptionalFilters = false;
  showSilences = false;

  solutionOptions: string[] = [];

  constructor(private alertService: AlertService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    forkJoin({
      alerts: this.alertService.getAlerts(),
      canonicalDefaults: this.alertService.getDefaultAlerts(),
      overrides: this.alertService.getOverrides(),
      blackouts: this.alertService.getBlackouts(),
      catalogApps: this.alertService.getCatalogApps(),
    }).subscribe({
      next: ({ alerts, canonicalDefaults, overrides, blackouts, catalogApps }) => {
        this.alerts = alerts;
        this.canonicalDefaults = canonicalDefaults;
        this.overrides = overrides;
        this.blackouts = blackouts;
        this.catalogApps = catalogApps;
        this.solutionOptions = catalogApps.map(a => a.name);
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

  get applicationSilences(): Blackout[] {
    if (!this.solutionName) return [];
    const sol = this.solutionName.toLowerCase();
    const variants = [sol, `${sol}-back`, `${sol}-front`];

    return this.blackouts.filter(b => b.matchers.some(m => {
      if (!APP_MATCHER_FIELDS.has(m.name) || !m.is_equal) return false;
      if (m.is_regex) {
        try {
          const re = new RegExp(m.value);
          return variants.some(v => re.test(v));
        } catch { return false; }
      }
      const val = m.value.toLowerCase();
      return variants.some(v => val === v || val.startsWith(`${v}-`));
    }));
  }

  toggleSilences(): void {
    this.showSilences = !this.showSilences;
  }

  formatSilenceDate(isoDate: string | null | undefined): string {
    if (!isoDate) return '';
    const d = new Date(isoDate);
    return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  matcherOperator(isRegex: boolean, isEqual: boolean): string {
    if (isRegex) return isEqual ? '=~' : '!~';
    return isEqual ? '=' : '!=';
  }

  private uniqueValues(values: (string | null | undefined)[]): string[] {
    return Array.from(new Set(values.filter((v): v is string => !!v))).sort();
  }

  private passesCommonFilters(alert: Alert): boolean {
    if (this.environment && !alert.environments.map(e => e.toLowerCase()).includes(this.environment)) return false;
    if (this.channel && (alert.notification_channel || '').toLowerCase() !== this.channel.toLowerCase()) return false;
    if (this.severity && (alert.severity || '').toLowerCase() !== this.severity) return false;
    return true;
  }

  private passesDefaultFilters(d: DefaultAlert): boolean {
    if (this.channel && (d.notification_channel || '').toLowerCase() !== this.channel.toLowerCase()) return false;
    if (this.severity && (d.severity || '').toLowerCase() !== this.severity) return false;
    return true;
  }

  get defaultAlerts(): DefaultAlertRow[] {
    if (!this.solutionName) return [];

    const overrideStatus = this.overrideStatusFor(this.solutionName);

    return this.canonicalDefaults
      .filter(d => this.passesDefaultFilters(d))
      .map(d => {
        const status = overrideStatus.get(d.raw_name) ?? { state: 'active' as const, excluded: [] };
        return {
          raw_name: d.raw_name,
          name: d.display_name,
          description: d.display_description,
          severity: d.severity,
          notification_channel: d.notification_channel,
          environments: ['pro'],
          is_overridden: status.state === 'disabled',
          is_partial: status.state === 'partial',
          chips: status.excluded,
          prometheus_name: d.raw_name,
        } satisfies DefaultAlertRow;
      });
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
      .map(alert => ({
        ...alert,
        chips: this.adhocChips(alert),
      }));
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

  get channelOptions(): string[] {
    if (!this.solutionName) return [];
    return this.uniqueValues(
      this.alerts.filter(a => a.solution === this.solutionName).map(a => a.notification_channel)
    );
  }

  get hasSolutionSelected(): boolean {
    return !!this.solutionName;
  }

  onSolutionChange(value: string): void {
    this.solutionName = value;
    this.channel = '';
    this.showSilences = false;
    this.cdr.detectChanges();
  }

  toggleOptionalFilters(): void {
    this.showOptionalFilters = !this.showOptionalFilters;
  }

  clearOptionalFilters(): void {
    this.environment = '';
    this.channel = '';
    this.severity = '';
  }

  environmentsLabel(envs: string[]): string {
    return envs && envs.length ? envs.join(', ') : '-';
  }
}
