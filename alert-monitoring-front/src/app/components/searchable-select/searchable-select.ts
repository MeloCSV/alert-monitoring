import { Component, Input, Output, EventEmitter, ElementRef, HostListener, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-searchable-select',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './searchable-select.html',
  styleUrl: './searchable-select.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SearchableSelectComponent {
  @Input() options: string[] = [];
  @Input() placeholder = '';
  @Input() value = '';
  @Output() valueChange = new EventEmitter<string>();

  open = false;
  query = '';

  constructor(private elementRef: ElementRef, private cdr: ChangeDetectorRef) {}

  get displayValue(): string {
    return this.open ? this.query : this.value;
  }

  get filteredOptions(): string[] {
    const q = this.query.trim().toLowerCase();
    if (!q) return this.options;
    return this.options.filter(opt => opt.toLowerCase().includes(q));
  }

  onFocus(): void {
    this.query = '';
    this.open = true;
  }

  onInput(value: string): void {
    this.query = value;
    this.open = true;
  }

  selectOption(option: string): void {
    this.value = option;
    this.valueChange.emit(option);
    this.open = false;
    this.query = '';
    this.cdr.markForCheck();
  }

  clear(event: Event): void {
    event.stopPropagation();
    this.value = '';
    this.query = '';
    this.valueChange.emit('');
    this.cdr.markForCheck();
  }

  @HostListener('document:click', ['$event'])
  onClickOutside(event: MouseEvent): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.open = false;
      this.query = '';
      this.cdr.markForCheck();
    }
  }
}