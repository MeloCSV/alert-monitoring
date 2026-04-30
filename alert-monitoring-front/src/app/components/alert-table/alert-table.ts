import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { AlertService, Alert } from '../../services/alert';

@Component({
  selector: 'app-alert-table',
  standalone: true,
  imports: [],
  templateUrl: './alert-table.html',
  styleUrl: './alert-table.scss'
})
export class AlertTableComponent implements OnInit {
  alerts: Alert[] = [];
  loading = true;
  error = false;

  constructor(private alertService: AlertService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.alertService.getAlerts().subscribe({
      next: (data) => {
        this.alerts = data;
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

  getSeverityClass(severity: string): string {
    switch (severity) {
      case 'critical': return 'badge-critical';
      case 'warning': return 'badge-warning';
      default: return 'badge-unknown';
    }
  }

  getConfidenceColor(confidence: number): string {
    if (confidence >= 0.7) return 'high';
    if (confidence >= 0.4) return 'medium';
    return 'low';
  }
}