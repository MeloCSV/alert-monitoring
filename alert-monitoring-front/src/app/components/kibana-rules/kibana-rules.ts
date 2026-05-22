import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import { AlertService, KibanaRule } from '../../services/alert';
import { SearchableSelectComponent } from '../searchable-select/searchable-select';

@Component({
  selector: 'app-kibana-rules',
  standalone: true,
  imports: [FormsModule, SearchableSelectComponent],
  templateUrl: './kibana-rules.html',
  styleUrl: './kibana-rules.scss'
})
export class KibanaRulesComponent implements OnInit {
  rules: KibanaRule[] = [];
  apiOptions: string[] = [];
  loading = true;
  error = false;

  selectedApi = '';

  constructor(private alertService: AlertService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    forkJoin({
      rules: this.alertService.getKibanaRules(),
      apis: this.alertService.getKibanaRuleApis(),
    }).subscribe({
      next: ({ rules, apis }) => {
        this.rules = rules;
        this.apiOptions = apis;
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

  get globalRules(): KibanaRule[] {
    return this.rules.filter(r => r.is_global);
  }

  get apiRules(): KibanaRule[] {
    if (!this.selectedApi) return [];
    const api = this.selectedApi.toLowerCase();
    return this.rules.filter(r => !r.is_global && r.apis.some(a => a.toLowerCase() === api));
  }

  onApiChange(value: string): void {
    this.selectedApi = value;
    this.cdr.detectChanges();
  }

  formatLastExecution(date: string | null): string {
    if (!date) return '-';
    try {
      return new Date(date).toLocaleString('es-ES', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch {
      return date;
    }
  }
}
