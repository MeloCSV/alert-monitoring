import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { AlertService, Alert, AlertOverride, Blackout, BlackoutMatcher, CatalogApp, DefaultAlert } from '../../services/alert';
import { SearchableSelectComponent } from '../searchable-select/searchable-select';

type EnvironmentFilter = '' | 'dev' | 'itg' | 'pre' | 'pro';
type SeverityFilter = '' | 'warning' | 'principal' | 'critical';

interface OverrideStatus {
  state: 'disabled' | 'partial' | 'active';
  excluded: string[];
}

interface BlackoutInfo {
  isFullySilenced: boolean;
  silencedEnvironments: string[];
  blackout: Blackout | null;
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
  is_blackout: boolean;
  blackout: Blackout | null;
  chips: string[];
  prometheus_name: string;
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

  private computeBlackoutInfoForDefault(defaultAlert: DefaultAlert, solution: string): BlackoutInfo {
    const alertEnvs = ['pro'];
    const namespaceValue = solution.toLowerCase();
    const labelGetters: Record<string, () => string> = {
      alertname:          () => defaultAlert.raw_name,
      severity:           () => (defaultAlert.severity || '').toLowerCase(),
      alertype:           () => 'default',
      namespace:          () => namespaceValue,
      exported_namespace: () => namespaceValue,
    };

    const silenced = new Set<string>();
    let noEnvSilenced = false;
    let representative: Blackout | null = null;

    for (const blackout of this.blackouts) {
      const nonEnvMatchers = blackout.matchers.filter(m => m.name in labelGetters);
      const envMatchers = blackout.matchers.filter(m => m.name === 'environment' || m.name === 'environments');
      if (nonEnvMatchers.length === 0 && envMatchers.length === 0) continue;

      if (!nonEnvMatchers.some(m => m.name === 'alertname')) continue;
      if (!nonEnvMatchers.some(m => m.name === 'namespace' || m.name === 'exported_namespace')) continue;

      const nonEnvOk = nonEnvMatchers.every(m =>
        this.matchesBlackoutValue(m.value, m.is_regex, m.is_equal, labelGetters[m.name]())
      );
      if (!nonEnvOk) continue;

      if (envMatchers.length === 0) {
        if (alertEnvs.length === 0) noEnvSilenced = true;
        else alertEnvs.forEach(e => silenced.add(e));
        if (representative === null) representative = blackout;
        continue;
      }

      for (const env of alertEnvs) {
        const candidates = this.envCandidatesFor(env);
        const envOk = envMatchers.every(m => this.matchArrayMatcher(m, candidates));
        if (envOk) {
          silenced.add(env);
          if (representative === null) representative = blackout;
        }
      }
    }

    const silencedList = alertEnvs.filter(e => silenced.has(e));
    const isFullySilenced = alertEnvs.length === 0
      ? noEnvSilenced
      : silencedList.length === alertEnvs.length && silencedList.length > 0;

    return { isFullySilenced, silencedEnvironments: silencedList, blackout: representative };
  }

  private computeBlackoutInfo(alert: Alert): BlackoutInfo {
    const isDefault = alert.alert_type === 'Por Defecto';
    const alertEnvs = (alert.environments || []).map(e => e.toLowerCase());
    const namespaceValue = (alert.microservice || alert.solution || '').toLowerCase();
    const labelGetters: Record<string, () => string> = {
      alertname: () => alert.prometheus_name || alert.name,
      severity:  () => (alert.severity || '').toLowerCase(),
      solucion:  () => (alert.solution || '').toLowerCase(),
      solution:  () => (alert.solution || '').toLowerCase(),
      alertype:  () => isDefault ? 'default' : 'adhoc',
      namespace: () => namespaceValue,
      exported_namespace: () => namespaceValue,
    };

    const silenced = new Set<string>();
    let noEnvSilenced = false;
    let representative: Blackout | null = null;

    for (const blackout of this.blackouts) {
      const nonEnvMatchers = blackout.matchers.filter(m => m.name in labelGetters);
      const envMatchers = blackout.matchers.filter(m => m.name === 'environment' || m.name === 'environments');
      if (nonEnvMatchers.length === 0 && envMatchers.length === 0) continue;

      if (isDefault) {
        if (!nonEnvMatchers.some(m => m.name === 'alertname')) continue;
        if (!nonEnvMatchers.some(m => m.name === 'namespace' || m.name === 'exported_namespace')) continue;
      }

      const nonEnvOk = nonEnvMatchers.every(m =>
        this.matchesBlackoutValue(m.value, m.is_regex, m.is_equal, labelGetters[m.name]())
      );
      if (!nonEnvOk) continue;

      if (envMatchers.length === 0) {
        if (alertEnvs.length === 0) noEnvSilenced = true;
        else alertEnvs.forEach(e => silenced.add(e));
        if (representative === null) representative = blackout;
        continue;
      }

      for (const env of alertEnvs) {
        const candidates = this.envCandidatesFor(env);
        const envOk = envMatchers.every(m => this.matchArrayMatcher(m, candidates));
        if (envOk) {
          silenced.add(env);
          if (representative === null) representative = blackout;
        }
      }
    }

    const silencedList = alertEnvs.filter(e => silenced.has(e));
    const isFullySilenced = alertEnvs.length === 0
      ? noEnvSilenced
      : silencedList.length === alertEnvs.length && silencedList.length > 0;

    return { isFullySilenced, silencedEnvironments: silencedList, blackout: representative };
  }

  private matchArrayMatcher(m: BlackoutMatcher, vals: string[]): boolean {
    if (vals.length === 0) return false;
    if (m.is_equal) {
      return vals.some(v => this.matchesBlackoutValue(m.value, m.is_regex, true, v));
    }
    return vals.every(v => this.matchesBlackoutValue(m.value, m.is_regex, false, v));
  }

  private envCandidatesFor(env: string): string[] {
    const e = env.toLowerCase();
    return [e, `ocp-${e}`, `gcp-${e}`];
  }

  partialBlackoutLabel(alert: Alert): string {
    const envs = alert.blackout_environments ?? [];
    if (envs.length === 1) return `Silenciada en entorno: ${envs[0]}`;
    return `Silenciada en entornos: ${envs.join(', ')}`;
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
    const solution = this.solutionName;

    return this.canonicalDefaults
      .filter(d => this.passesDefaultFilters(d))
      .map(d => {
        const status = overrideStatus.get(d.raw_name) ?? { state: 'active' as const, excluded: [] };
        const blackoutInfo = this.computeBlackoutInfoForDefault(d, solution);
        return {
          raw_name: d.raw_name,
          name: d.display_name,
          description: d.display_description,
          severity: d.severity,
          notification_channel: d.notification_channel,
          environments: ['pro'],
          is_overridden: status.state === 'disabled',
          is_partial: status.state === 'partial',
          is_blackout: blackoutInfo.isFullySilenced,
          blackout: blackoutInfo.blackout,
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
      .map(alert => {
        const blackoutInfo = this.computeBlackoutInfo(alert);
        return {
          ...alert,
          is_blackout: blackoutInfo.isFullySilenced,
          is_partial_blackout: !blackoutInfo.isFullySilenced && blackoutInfo.silencedEnvironments.length > 0,
          blackout_environments: blackoutInfo.silencedEnvironments,
          blackout: blackoutInfo.blackout,
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
