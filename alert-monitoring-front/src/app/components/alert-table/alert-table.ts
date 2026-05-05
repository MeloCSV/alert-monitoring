import { Component, OnInit, ChangeDetectorRef, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AlertService, Alert } from '../../services/alert';
import { SearchableSelectComponent } from '../searchable-select/searchable-select';

type SeverityFilter = '' | 'warning' | 'critical' | 'principal';
type EnvironmentFilter = '' | 'dev' | 'itg' | 'pre' | 'pro';
type AlertTypeFilter = '' | 'Por Defecto' | 'Ad-hoc';
type SourceToolFilter = '' | 'prometheus' | 'elastic';
type OverriddenFilter = '' | 'yes' | 'no';

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

  alarmName = '';
  solutionName = '';
  microserviceName = '';
  environment: EnvironmentFilter = '';
  severity: SeverityFilter = '';
  alertType: AlertTypeFilter = '';
  globalSearch = '';

  showAdvanced = false;
  sourceTool: SourceToolFilter = '';
  isOverridden: OverriddenFilter = '';

  alarmNameOptions: string[] = [];
  solutionOptions: string[] = [];
  microserviceOptions: string[] = [];

  constructor(private alertService: AlertService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.alertService.getAlerts().subscribe({
      next: (data) => {
        this.alerts = data;
        this.alarmNameOptions = this.uniqueValues(data.map(a => a.name));
        this.solutionOptions = this.uniqueValues(data.map(a => a.solution));
        this.microserviceOptions = this.uniqueValues(data.map(a => a.microservice));
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

  get filteredAlerts(): Alert[] {
    const search = this.globalSearch.trim().toLowerCase();
    return this.alerts.filter(alert => {
      if (this.alarmName && alert.name !== this.alarmName) return false;
      if (this.solutionName && alert.solution !== this.solutionName) return false;
      if (this.microserviceName && alert.microservice !== this.microserviceName) return false;
      if (this.environment && !alert.environments.map(e => e.toLowerCase()).includes(this.environment)) return false;
      if (this.severity && alert.severity.toLowerCase() !== this.severity) return false;
      if (this.alertType && alert.alert_type !== this.alertType) return false;
      if (this.sourceTool && (alert.source_tool || '').toLowerCase() !== this.sourceTool) return false;
      if (this.isOverridden === 'yes' && !alert.is_overridden) return false;
      if (this.isOverridden === 'no' && alert.is_overridden) return false;
      if (search) {
        const haystack = [alert.name, alert.solution, alert.microservice]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        if (!haystack.includes(search)) return false;
      }
      return true;
    });
  }

  toggleAdvanced(): void {
    this.showAdvanced = !this.showAdvanced;
  }

  triggerSearch(): void {
    this.cdr.detectChanges();
  }

  getSeverityClass(severity: string): string {
    switch ((severity || '').toLowerCase()) {
      case 'critical': return 'badge-critical';
      case 'warning': return 'badge-warning';
      case 'principal': return 'badge-principal';
      default: return 'badge-unknown';
    }
  }

  getAlertTypeClass(type: string): string {
    return type === 'Por Defecto' ? 'badge-default' : 'badge-adhoc';
  }

  alertTypeLabel(type: string): string {
    return type === 'Por Defecto' ? 'Por defecto' : 'Ad hoc';
  }

  getConfidenceColor(confidence: number): string {
    if (confidence >= 0.7) return 'high';
    if (confidence >= 0.4) return 'medium';
    return 'low';
  }
}