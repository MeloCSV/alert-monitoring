import { Component } from '@angular/core';
import { AlertTableComponent } from './components/alert-table/alert-table';
import { KibanaRulesComponent } from './components/kibana-rules/kibana-rules';

type ActiveTab = 'alerts' | 'kibana-rules';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [AlertTableComponent, KibanaRulesComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  activeTab: ActiveTab = 'alerts';

  select(tab: ActiveTab): void {
    this.activeTab = tab;
  }
}
