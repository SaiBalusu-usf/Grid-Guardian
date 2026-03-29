import type { DemoScenario } from './types';

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'severe-storm',
    name: 'Severe Storm',
    description:
      'Hurricane watch near USF campus and Tampa General Hospital corridor. High winds, storm surge, potential flooding across Tampa Bay.',
    icon: '\u26C8\uFE0F',
    scenario:
      'Hurricane watch with severe thunderstorms near USF campus and Tampa General Hospital. Wind speeds 85mph, storm surge warning, flash flood warning across Hillsborough County.',
    trigger_source: 'weather_alert',
  },
  {
    id: 'grid-outage',
    name: 'Grid Outage',
    description:
      'Major power grid failure affecting Tampa shelters, hospitals, and critical infrastructure. Backup generators failing in sequence.',
    icon: '\uD83D\uDD0C',
    scenario:
      'Widespread power grid failure across downtown Tampa and Davis Islands medical district. Multiple TECO substations offline, backup generators at Tampa General and St. Joseph\'s failing. 15,000+ residents without power.',
    trigger_source: 'grid_monitor',
  },
  {
    id: 'multi-zone-emergency',
    name: 'Multi-Zone Emergency',
    description:
      'Cascading disaster across Tampa Bay requiring coordinated shelter operations, evacuations, and resource deployment.',
    icon: '\uD83D\uDEA8',
    scenario:
      'Multi-zone emergency across Tampa Bay: storm surge flooding in South Tampa, structural collapse in Ybor City, hazmat spill near Port Tampa. 5 shelters activating, Tampa General on diversion. Estimated 12,000 affected residents.',
    trigger_source: 'emergency_dispatch',
  },
];
