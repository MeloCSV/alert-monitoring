import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AlertService, Alert, Blackout, DefaultAlertView } from '../../services/alert';
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
  solutionOptions: string[] = [];

  private adhocData: Alert[] = [];
  private defaultData: DefaultAlertView[] = [];
  private allBlackouts: Blackout[] = [];
  channels: string[] = [];

  loading = true;
  error = false;
  solutionLoading = false;
  solutionError = false;

  solutionName = '';

  environment: EnvironmentFilter = '';
  channel = '';
  severity: SeverityFilter = '';

  showOptionalFilters = false;
  showSilences = false;

  constructor(private alertService: AlertService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
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
    this.allBlackouts = [];
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

    this.alertService.getBlackouts(value).subscribe({
      next: (blackouts) => {
        this.allBlackouts = blackouts;
        this.cdr.detectChanges();
      }
    });
  }

  get applicationSilences(): Blackout[] {
    return this.allBlackouts;
  }

  get defaultAlerts(): DefaultAlertView[] {
    return this.defaultData.filter(d => this.passesDefaultFilters(d));
  }

  get adhocAlerts(): Alert[] {
    return this.adhocData.filter(alert => this.passesCommonFilters(alert));
  }

  get channelOptions(): string[] {
    return this.channels;
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
