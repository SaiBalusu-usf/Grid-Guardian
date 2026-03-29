import type { DemoScenario } from './types';

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'severe-storm',
    name: 'Severe Storm',
    description:
      'Tornado watch near university campus and hospital corridor. High winds, hail, potential flooding across multiple zones.',
    icon: '\u26C8\uFE0F',
    scenario:
      'Severe thunderstorm with tornado watch near campus and hospital corridor. Wind speeds 75mph, large hail, flash flood warning.',
    trigger_source: 'weather_alert',
  },
  {
    id: 'grid-outage',
    name: 'Grid Outage',
    description:
      'Major power grid failure affecting shelters, hospitals, and critical infrastructure. Backup generators failing in sequence.',
    icon: '\uD83D\uDD0C',
    scenario:
      'Widespread power grid failure across downtown and medical district. Multiple substations offline, backup generators at 3 hospitals failing. 12,000+ residents without power.',
    trigger_source: 'grid_monitor',
  },
  {
    id: 'multi-zone-emergency',
    name: 'Multi-Zone Emergency',
    description:
      'Cascading disaster across multiple zones requiring coordinated shelter operations, evacuations, and resource deployment.',
    icon: '\uD83D\uDEA8',
    scenario:
      'Multi-zone emergency: flooding in Zone A, structural collapse in Zone B, hazmat spill in Zone C. 5 shelters activating, 3 hospitals on diversion. Estimated 8,000 affected residents.',
    trigger_source: 'emergency_dispatch',
  },
];
