import { ComponentFixture, TestBed } from '@angular/core/testing';
import { vi } from 'vitest';

import { SearchableSelectComponent } from './searchable-select';

describe('SearchableSelectComponent', () => {
  let component: SearchableSelectComponent;
  let fixture: ComponentFixture<SearchableSelectComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SearchableSelectComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SearchableSelectComponent);
    component = fixture.componentInstance;
    component.options = ['my-app', 'other-app', 'third-app'];
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('displayValue', () => {
    it('should return the selected value when closed', () => {
      component.value = 'my-app';
      component.open = false;

      expect(component.displayValue).toBe('my-app');
    });

    it('should return the current query when open', () => {
      component.value = 'my-app';
      component.open = true;
      component.query = 'oth';

      expect(component.displayValue).toBe('oth');
    });
  });

  describe('filteredOptions', () => {
    it('should return all options when the query is empty', () => {
      component.query = '';

      expect(component.filteredOptions).toEqual(['my-app', 'other-app', 'third-app']);
    });

    it('should filter options case-insensitively by the query', () => {
      component.query = 'OTHER';

      expect(component.filteredOptions).toEqual(['other-app']);
    });

    it('should ignore leading/trailing whitespace in the query', () => {
      component.query = '  third  ';

      expect(component.filteredOptions).toEqual(['third-app']);
    });
  });

  describe('onFocus', () => {
    it('should clear the query and open the dropdown', () => {
      component.query = 'stale';
      component.open = false;

      component.onFocus();

      expect(component.query).toBe('');
      expect(component.open).toBe(true);
    });
  });

  describe('onInput', () => {
    it('should update the query and open the dropdown', () => {
      component.open = false;

      component.onInput('my');

      expect(component.query).toBe('my');
      expect(component.open).toBe(true);
    });
  });

  describe('selectOption', () => {
    it('should set the value, emit it and close the dropdown', () => {
      const emitted: string[] = [];
      component.valueChange.subscribe((v) => emitted.push(v));
      component.open = true;
      component.query = 'oth';

      component.selectOption('other-app');

      expect(component.value).toBe('other-app');
      expect(emitted).toEqual(['other-app']);
      expect(component.open).toBe(false);
      expect(component.query).toBe('');
    });
  });

  describe('clear', () => {
    it('should stop propagation, reset the value and emit an empty string', () => {
      const emitted: string[] = [];
      component.valueChange.subscribe((v) => emitted.push(v));
      component.value = 'my-app';
      component.query = 'my';
      const event = new MouseEvent('click');
      const stopPropagationSpy = vi.spyOn(event, 'stopPropagation');

      component.clear(event);

      expect(stopPropagationSpy).toHaveBeenCalled();
      expect(component.value).toBe('');
      expect(component.query).toBe('');
      expect(emitted).toEqual(['']);
    });
  });

  describe('onClickOutside', () => {
    it('should close the dropdown when the click is outside the component', () => {
      component.open = true;
      component.query = 'my';
      const outsideTarget = document.createElement('div');
      document.body.appendChild(outsideTarget);

      component.onClickOutside({ target: outsideTarget } as unknown as MouseEvent);

      expect(component.open).toBe(false);
      expect(component.query).toBe('');

      document.body.removeChild(outsideTarget);
    });

    it('should keep the dropdown open when the click is inside the component', () => {
      component.open = true;
      component.query = 'my';
      const insideTarget = fixture.nativeElement as HTMLElement;

      component.onClickOutside({ target: insideTarget } as unknown as MouseEvent);

      expect(component.open).toBe(true);
      expect(component.query).toBe('my');
    });
  });
});
