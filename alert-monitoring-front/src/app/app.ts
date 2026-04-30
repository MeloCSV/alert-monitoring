import { Component } from '@angular/core';
import { AlertTableComponent } from './components/alert-table/alert-table';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [AlertTableComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {}