import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { AlertService, Alert, AlertOverride, Blackout, BlackoutMatcher, DefaultAlertRule } from '../../services/alert';
import { SearchableSelectComponent } from '../searchable-select/searchable-select';

type SeverityFilter = '' | 'warning' | 'critical' | 'principal';
type EnvironmentFilter = '' | 'dev' | 'itg' | 'pre' | 'pro';

interface OverrideStatus {
  state: 'disabled' | 'partial' | 'active';
  excluded: string[];
}

interface BlackoutInfo {
  isFullySilenced: boolean;
  silencedEnvironments: string[];
  blackout: Blackout | null;
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
  defaultCatalog: DefaultAlertRule[] = [];
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
      defaultCatalog: this.alertService.getDefaultCatalog(),
      overrides: this.alertService.getOverrides(),
      blackouts: this.alertService.getBlackouts(),
    }).subscribe({
      next: ({ alerts, defaultCatalog, overrides, blackouts }) => {
        this.alerts = alerts;
        this.defaultCatalog = defaultCatalog;
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

  private computeBlackoutInfo(alert: Alert): BlackoutInfo {
    const isDefault = alert.alert_type === 'Por Defecto';
    const alertEnvs = (alert.environments || []).map(e => e.toLowerCase());
    const namespaceValue = isDefault
      ? (this.solutionName || '').toLowerCase()
      : (alert.microservice || '').toLowerCase();
    const labelGetters: Record<string, () => string> = {
      alertname: () => alert.name,
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
    if (this.severity && alert.severity.toLowerCase() !== this.severity) return false;
    return true;
  }

  get defaultAlerts(): Alert[] {
    if (!this.solutionName) return [];

    // Clusters where this solution has Prometheus ad-hoc alerts
    const clustersWithSolution = new Set(
      this.alerts
        .filter(a => a.source_tool === 'Prometheus' && a.solution === this.solutionName && a.cluster)
        .map(a => a.cluster!)
    );

    // Filter catalog to matching clusters and apply common filters, then deduplicate by name
    // (the same default alert may appear in both normal and criticas groups or across clusters)
    const seenNames = new Set<string>();
    const catalogEntries = this.defaultCatalog.filter(r => {
      if (clustersWithSolution.size > 0 && !clustersWithSolution.has(r.cluster)) return false;
      if (this.environment && !r.environments.map(e => e.toLowerCase()).includes(this.environment)) return false;
      if (this.severity && r.severity.toLowerCase() !== this.severity) return false;
      if (seenNames.has(r.name)) return false;
      seenNames.add(r.name);
      return true;
    });

    const overrideStatus = this.overrideStatusFor(this.solutionName);
    return catalogEntries.map(rule => {
      // Use technical name for override and blackout lookup; display_name for the UI
      const status = overrideStatus.get(rule.name) ?? { state: 'active', excluded: [] };
      const proxy: Alert = {
        name: rule.name,
        description: rule.description,
        source_tool: 'Prometheus',
        severity: rule.severity,
        condition: rule.condition,
        environments: rule.environments,
        microservice: null,
        solution: this.solutionName,
        notification_channel: rule.notification_channel,
        alert_type: 'Por Defecto',
        cluster: rule.cluster,
      };
      const blackoutInfo = this.computeBlackoutInfo(proxy);
      return {
        ...proxy,
        name: rule.display_name,
        is_overridden: status.state === 'disabled',
        is_partial: status.state === 'partial',
        is_blackout: blackoutInfo.isFullySilenced,
        is_partial_blackout: false,
        blackout_environments: [],
        blackout: blackoutInfo.blackout,
        chips: status.excluded,
      };
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
