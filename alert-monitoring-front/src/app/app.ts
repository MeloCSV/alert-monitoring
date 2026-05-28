import { Component } from '@angular/core';
import { AlertTableComponent } from './components/alert-table/alert-table';

type ActiveTab = 'alerts' | 'kibana-rules';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [AlertTableComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  activeTab: ActiveTab = 'alerts';

  select(tab: ActiveTab): void {
    this.activeTab = tab;
  }
}
