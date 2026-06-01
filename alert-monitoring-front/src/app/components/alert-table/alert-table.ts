import { Component, Input, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AlertService, Alert, AlertApi, ApiSolutionView, Blackout, DefaultAlertView, DefaultAlertApiView, KibanaRule } from '../../services/alert';
import { SearchableSelectComponent } from '../searchable-select/searchable-select';

type EnvironmentFilter = '' | 'dev' | 'itg' | 'pre' | 'pro';
type SeverityFilter = '' | 'warning' | 'principal' | 'critical';

@Component({
  selector: 'app-alert-table',
  standalone: true,
  imports: [FormsModule, SearchableSelectComponent],
  templateUrl: './alert-table.html',
  styleUrl: './alert-table.scss'
})
export class AlertTableComponent implements OnInit {
  @Input() mode: 'apps' | 'apis' = 'apps';

  // Apps state
  solutionOptions: string[] = [];
  private adhocData: Alert[] = [];
  private defaultData: DefaultAlertView[] = [];
  private allBlackouts: Blackout[] = [];
  channels: string[] = [];
  solutionLoading = false;
  solutionError = false;
  solutionName = '';
  showSilences = false;
  environment: EnvironmentFilter = '';

  // APIs state
  apiSolutionName = '';
  private apiDefaultData: DefaultAlertApiView[] = [];
  private apiAdhocData: AlertApi[] = [];
  apiChannels: string[] = [];
  apiSolutionLoading = false;
  apiSolutionError = false;

  // Shared state
  loading = true;
  error = false;
  channel = '';
  severity: SeverityFilter = '';
  showOptionalFilters = false;

  // Keep KibanaRule for backward compat (unused in new mode but kept to avoid import errors)
  rules: KibanaRule[] = [];

  constructor(private alertService: AlertService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    if (this.mode === 'apps') {
      this.alertService.getCatalogApps().subscribe({
        next: (apps) => {
          this.solutionOptions = apps.map(a => a.name);
          this.loading = false;
          this.cdr.detectChanges();
        },
        error: () => {
          this.error = true;
          this.loading = false;
          this.cdr.detectChanges();
        }
      });

      this.alertService.getBlackouts().subscribe({
        next: (blackouts) => {
          this.allBlackouts = blackouts;
          this.cdr.detectChanges();
        }
      });
    } else {
      this.alertService.getCatalogApps().subscribe({
        next: (apps) => {
          this.solutionOptions = apps.map(a => a.name);
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
  }

  // Apps methods

  onSolutionChange(value: string): void {
    this.solutionName = value;
    this.channel = '';
    this.showSilences = false;
    this.solutionError = false;

    if (!value) {
      this.adhocData = [];
      this.defaultData = [];
      this.channels = [];
      this.solutionLoading = false;
      this.cdr.detectChanges();
      return;
    }

    this.solutionLoading = true;
    this.cdr.detectChanges();

    this.alertService.getSolutionView(value).subscribe({
      next: (view) => {
        this.defaultData = view.default_alerts;
        this.adhocData = view.adhoc_alerts;
        this.channels = view.channels;
        this.solutionLoading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.solutionError = true;
        this.solutionLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  get applicationSilences(): Blackout[] {
    if (!this.solutionName) return [];
    const sol = this.solutionName.toLowerCase();
    const variants = [sol, `${sol}-back`, `${sol}-front`];
    const appFields = new Set(['namespace', 'solucion', 'solution', 'exported_namespace',
      'backend_target_name', 'deployment', 'replicaset', 'cronjob', 'pod']);
    return this.allBlackouts.filter(b =>
      b.matchers.some(m => {
        if (!appFields.has(m.name) || !m.is_equal) return false;
        if (m.is_regex) {
          try {
            const re = new RegExp(m.value, 'i');
            return variants.some(v => re.test(v));
          } catch { return false; }
        }
        const val = m.value.toLowerCase();
        return variants.some(v => val === v || val.startsWith(`${v}-`));
      })
    );
  }

  get defaultAlerts(): DefaultAlertView[] {
    return this.defaultData.filter(d => this.passesDefaultFilters(d));
  }

  get adhocAlerts(): Alert[] {
    return this.adhocData.filter(alert => this.passesCommonFilters(alert));
  }

  get hasSolutionSelected(): boolean {
    return !!this.solutionName;
  }

  private passesCommonFilters(alert: Alert): boolean {
    if (this.environment && !alert.environments.map(e => e.toLowerCase()).includes(this.environment)) return false;
    if (this.channel && (alert.notification_channel || '').toLowerCase() !== this.channel.toLowerCase()) return false;
    if (this.severity && (alert.severity || '').toLowerCase() !== this.severity) return false;
    return true;
  }

  private passesDefaultFilters(d: DefaultAlertView): boolean {
    if (this.channel && (d.notification_channel || '').toLowerCase() !== this.channel.toLowerCase()) return false;
    if (this.severity && (d.severity || '').toLowerCase() !== this.severity) return false;
    return true;
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

  environmentsLabel(envs: string[]): string {
    return envs && envs.length ? envs.join(', ') : '-';
  }

  // APIs methods

  onApiSolutionChange(value: string): void {
    this.apiSolutionName = value;
    this.channel = '';
    this.apiSolutionError = false;

    if (!value) {
      this.apiDefaultData = [];
      this.apiAdhocData = [];
      this.apiChannels = [];
      this.apiSolutionLoading = false;
      this.cdr.detectChanges();
      return;
    }

    this.apiSolutionLoading = true;
    this.cdr.detectChanges();

    this.alertService.getApiSolutionView(value).subscribe({
      next: (view) => {
        this.apiDefaultData = view.default_alerts;
        this.apiAdhocData = view.adhoc_alerts;
        this.apiChannels = view.channels;
        this.apiSolutionLoading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.apiSolutionError = true;
        this.apiSolutionLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  get hasApiSolutionSelected(): boolean {
    return !!this.apiSolutionName;
  }

  get apiDefaultAlerts(): DefaultAlertApiView[] {
    return this.apiDefaultData.filter(d => this.passesApiDefaultFilters(d));
  }

  get apiAdhocAlerts(): AlertApi[] {
    return this.apiAdhocData.filter(a => this.passesApiAdhocFilters(a));
  }

  private passesApiDefaultFilters(d: DefaultAlertApiView): boolean {
    if (this.channel && (d.notification_channel || '').toLowerCase() !== this.channel.toLowerCase()) return false;
    if (this.severity && (d.severity || '').toLowerCase() !== this.severity) return false;
    return true;
  }

  private passesApiAdhocFilters(a: AlertApi): boolean {
    if (this.channel && (a.notification_channel || '').toLowerCase() !== this.channel.toLowerCase()) return false;
    if (this.severity && (a.severity || '').toLowerCase() !== this.severity) return false;
    return true;
  }

  get channelOptions(): string[] {
    if (this.mode === 'apis') {
      return this.apiChannels;
    }
    return this.channels;
  }

  // Shared methods

  toggleOptionalFilters(): void {
    this.showOptionalFilters = !this.showOptionalFilters;
  }

  clearOptionalFilters(): void {
    this.environment = '';
    this.channel = '';
    this.severity = '';
  }
}
