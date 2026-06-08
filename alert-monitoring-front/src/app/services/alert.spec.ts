import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { HttpTestingController } from '@angular/common/http/testing';

import { AlertService, CatalogApp, SolutionView, Blackout, ApiSolutionView } from './alert';

describe('AlertService', () => {
  let service: AlertService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AlertService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getCatalogApps', () => {
    it('should GET catalog apps from /catalog', () => {
      const mockApps: CatalogApp[] = [
        { object_id: '1', name: 'my-app' },
        { object_id: '2', name: 'other-app' },
      ];

      service.getCatalogApps().subscribe((apps) => {
        expect(apps.length).toBe(2);
        expect(apps[0].name).toBe('my-app');
      });

      const req = httpMock.expectOne('http://localhost:8080/catalog');
      expect(req.request.method).toBe('GET');
      req.flush(mockApps);
    });
  });

  describe('getSolutionView', () => {
    it('should GET solution view with solution query param', () => {
      const mockView: SolutionView = {
        solution: 'my-app',
        default_alerts: [],
        adhoc_alerts: [],
        channels: ['Microsoft Teams'],
      };

      service.getSolutionView('my-app').subscribe((view) => {
        expect(view.channels).toEqual(['Microsoft Teams']);
      });

      const req = httpMock.expectOne(
        (r) => r.url === 'http://localhost:8080/alerts/view' && r.params.get('solution') === 'my-app'
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockView);
    });
  });

  describe('getBlackouts', () => {
    it('should GET blackouts without params when solution is not provided', () => {
      const mockBlackouts: Blackout[] = [];

      service.getBlackouts().subscribe((b) => {
        expect(b).toEqual([]);
      });

      const req = httpMock.expectOne('http://localhost:8080/alerts/blackouts');
      expect(req.request.method).toBe('GET');
      req.flush(mockBlackouts);
    });

    it('should GET blackouts with solution query param when provided', () => {
      const mockBlackouts: Blackout[] = [
        {
          id: 'abc-123',
          matchers: [{ name: 'namespace', value: 'my-app', is_regex: false, is_equal: true }],
        },
      ];

      service.getBlackouts('my-app').subscribe((b) => {
        expect(b.length).toBe(1);
        expect(b[0].id).toBe('abc-123');
      });

      const req = httpMock.expectOne(
        (r) => r.url === 'http://localhost:8080/alerts/blackouts' && r.params.get('solution') === 'my-app'
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockBlackouts);
    });
  });

  describe('getApiSolutionView', () => {
    it('should GET api solution view with app query param', () => {
      const mockView: ApiSolutionView = {
        app: 'my-app',
        default_alerts: [],
        adhoc_alerts: [],
        api_microservice_map: { 'absence': 'absence-back' },
        channels: ['ServiceNow'],
      };

      service.getApiSolutionView('my-app').subscribe((view) => {
        expect(view.app).toBe('my-app');
        expect(view.api_microservice_map['absence']).toBe('absence-back');
      });

      const req = httpMock.expectOne(
        (r) => r.url === 'http://localhost:8080/alerts/api-view' && r.params.get('app') === 'my-app'
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockView);
    });
  });
});
