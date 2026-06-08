import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { AlertTableComponent } from './alert-table';
import { AlertService, CatalogApp, SolutionView } from '../../services/alert';

const MOCK_CATALOG_APPS: CatalogApp[] = [
  { object_id: '1', name: 'my-app' },
  { object_id: '2', name: 'other-app' },
];

const MOCK_SOLUTION_VIEW: SolutionView = {
  solution: 'my-app',
  default_alerts: [
    {
      raw_name: 'Default_Status',
      name: 'Estado del servicio',
      description: null,
      severity: 'warning',
      notification_channel: 'Microsoft Teams',
      environments: ['pro'],
      is_disabled: false,
      is_partial: false,
      chips: [],
    },
  ],
  adhoc_alerts: [
    {
      name: 'Errores 500',
      description: 'Demasiados errores 500',
      source_tool: 'Prometheus',
      severity: 'critical',
      environments: ['pro'],
      microservice: 'my-app-back',
      solution: 'my-app',
      notification_channel: 'ServiceNow',
      alert_type: 'Ad-hoc',
      cluster: null,
      prometheus_name: null,
      chips: ['my-app-back'],
    },
  ],
  channels: ['Microsoft Teams', 'ServiceNow'],
};

describe('AlertTableComponent', () => {
  let component: AlertTableComponent;
  let fixture: ComponentFixture<AlertTableComponent>;
  let alertServiceMock: {
    getCatalogApps: ReturnType<typeof vi.fn>;
    getSolutionView: ReturnType<typeof vi.fn>;
    getBlackouts: ReturnType<typeof vi.fn>;
    getApiSolutionView: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    alertServiceMock = {
      getCatalogApps: vi.fn().mockReturnValue(of(MOCK_CATALOG_APPS)),
      getSolutionView: vi.fn().mockReturnValue(of(MOCK_SOLUTION_VIEW)),
      getBlackouts: vi.fn().mockReturnValue(of([])),
      getApiSolutionView: vi.fn().mockReturnValue(of({ app: '', default_alerts: [], adhoc_alerts: [], api_microservice_map: {}, channels: [] })),
    };

    await TestBed.configureTestingModule({
      imports: [AlertTableComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AlertService, useValue: alertServiceMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AlertTableComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load catalog apps on init and populate solutionOptions', () => {
    expect(alertServiceMock.getCatalogApps).toHaveBeenCalled();
    expect(component.solutionOptions).toEqual(['my-app', 'other-app']);
  });

  it('should set loading false after catalog apps are loaded', () => {
    expect(component.loading).toBe(false);
  });

  it('should set error true when catalog apps load fails', async () => {
    alertServiceMock.getCatalogApps.mockReturnValue(throwError(() => new Error('Network error')));

    fixture = TestBed.createComponent(AlertTableComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();

    expect(component.error).toBe(true);
    expect(component.loading).toBe(false);
  });

  describe('onSolutionChange', () => {
    it('should load solution view when solution is selected', () => {
      component.onSolutionChange('my-app');
      fixture.detectChanges();

      expect(alertServiceMock.getSolutionView).toHaveBeenCalledWith('my-app');
    });

    it('should reset data when empty string is passed', () => {
      component.onSolutionChange('');

      expect(component['adhocData']).toEqual([]);
      expect(component['defaultData']).toEqual([]);
      expect(component.channels).toEqual([]);
    });

    it('should set solutionError true on service error', async () => {
      alertServiceMock.getSolutionView.mockReturnValue(throwError(() => new Error('Server error')));

      component.onSolutionChange('my-app');
      await fixture.whenStable();

      expect(component.solutionError).toBe(true);
    });

    it('should update channels after loading solution view', async () => {
      component.onSolutionChange('my-app');
      await fixture.whenStable();

      expect(component.channels).toEqual(['Microsoft Teams', 'ServiceNow']);
    });
  });

  describe('filter getters', () => {
    beforeEach(async () => {
      component.onSolutionChange('my-app');
      await fixture.whenStable();
    });

    it('should return all adhoc alerts when no filters are active', () => {
      expect(component.adhocAlerts.length).toBe(1);
    });

    it('should filter adhoc alerts by severity', () => {
      component.severity = 'warning';
      expect(component.adhocAlerts.length).toBe(0);

      component.severity = 'critical';
      expect(component.adhocAlerts.length).toBe(1);
    });

    it('should filter adhoc alerts by channel', () => {
      component.channel = 'ServiceNow';
      expect(component.adhocAlerts.length).toBe(1);

      component.channel = 'Microsoft Teams';
      expect(component.adhocAlerts.length).toBe(0);
    });

    it('should filter adhoc alerts by environment', () => {
      component.environment = 'pro';
      expect(component.adhocAlerts.length).toBe(1);

      component.environment = 'dev';
      expect(component.adhocAlerts.length).toBe(0);
    });

    it('should return all default alerts when no filters are active', () => {
      component.severity = '';
      component.channel = '';
      expect(component.defaultAlerts.length).toBe(1);
    });

    it('should filter default alerts by channel', () => {
      component.channel = 'Microsoft Teams';
      expect(component.defaultAlerts.length).toBe(1);

      component.channel = 'ServiceNow';
      expect(component.defaultAlerts.length).toBe(0);
    });
  });

  describe('hasSolutionSelected', () => {
    it('should return false when no solution is selected', () => {
      expect(component.hasSolutionSelected).toBe(false);
    });

    it('should return true when a solution is selected', async () => {
      component.onSolutionChange('my-app');
      await fixture.whenStable();

      expect(component.hasSolutionSelected).toBe(true);
    });
  });

  describe('formatSilenceDate', () => {
    it('should return empty string for null input', () => {
      expect(component.formatSilenceDate(null)).toBe('');
    });

    it('should format ISO date to dd/mm/yyyy', () => {
      const result = component.formatSilenceDate('2025-06-15T00:00:00Z');
      expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    });
  });

  describe('matcherOperator', () => {
    it('should return = for exact string match', () => {
      expect(component.matcherOperator(false, true)).toBe('=');
    });

    it('should return != for exact string non-match', () => {
      expect(component.matcherOperator(false, false)).toBe('!=');
    });

    it('should return =~ for regex match', () => {
      expect(component.matcherOperator(true, true)).toBe('=~');
    });

    it('should return !~ for regex non-match', () => {
      expect(component.matcherOperator(true, false)).toBe('!~');
    });
  });

  describe('clearOptionalFilters', () => {
    it('should reset all optional filters to empty strings', () => {
      component.environment = 'pro';
      component.channel = 'ServiceNow';
      component.severity = 'critical';

      component.clearOptionalFilters();

      expect(component.environment).toBe('');
      expect(component.channel).toBe('');
      expect(component.severity).toBe('');
    });
  });
});
