'use client';

import { DEMO_SCENARIOS } from '@/lib/scenarios';
import SimulationButton from './SimulationButton';

export default function DemoScenarios() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {DEMO_SCENARIOS.map((s) => (
        <div
          key={s.id}
          className="group relative rounded-xl border border-slate-700/50 bg-slate-800/40 p-5 transition-all duration-300 hover:bg-slate-800/70 hover:border-slate-600/50 hover:shadow-xl hover:shadow-black/20"
        >
          <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none" />

          <div className="relative">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">{s.icon}</span>
              <h3 className="text-base font-semibold text-white">{s.name}</h3>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed mb-4 min-h-[3rem]">
              {s.description}
            </p>

            <SimulationButton scenario={s.scenario} triggerSource={s.trigger_source}>
              Launch Scenario
            </SimulationButton>
          </div>
        </div>
      ))}
    </div>
  );
}
