import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AlertTable } from './alert-table';

describe('AlertTable', () => {
  let component: AlertTable;
  let fixture: ComponentFixture<AlertTable>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlertTable],
    }).compileComponents();

    fixture = TestBed.createComponent(AlertTable);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
