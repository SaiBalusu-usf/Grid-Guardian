'use client';

import { Shield, Cpu, Network, Radio, Eye, Bell, Truck, Users, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import DemoScenarios from '@/components/DemoScenarios';

const AGENTS = [
  {
    name: 'Hazard Watcher',
    icon: Eye,
    color: 'red',
    description: 'Reads weather/hazard signals and produces severity, confidence, and impacted zones',
  },
  {
    name: 'Vulnerability Mapper',
    icon: Users,
    color: 'amber',
    description: 'Scores hospitals, shelters, elderly zones, and produces priority areas with equity notes',
  },
  {
    name: 'Route Planner',
    icon: Network,
    color: 'blue',
    description: 'Analyzes routing data to produce safe routes, closures, and travel risk assessments',
  },
  {
    name: 'Resource Coordinator',
    icon: Truck,
    color: 'emerald',
    description: 'Recommends crews, supplies, generators, batteries, and task priority',
  },
  {
    name: 'Public Alert',
    icon: Bell,
    color: 'purple',
    description: 'Drafts bilingual English/Spanish alerts with concise, actionable public messaging',
  },
];

const colorMap: Record<string, { bg: string; border: string; text: string; glow: string }> = {
  emerald: {
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
    glow: 'group-hover:shadow-emerald-500/10',
  },
  blue: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
    glow: 'group-hover:shadow-blue-500/10',
  },
  amber: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    glow: 'group-hover:shadow-amber-500/10',
  },
  red: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
    glow: 'group-hover:shadow-red-500/10',
  },
  purple: {
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/30',
    text: 'text-purple-400',
    glow: 'group-hover:shadow-purple-500/10',
  },
};

export default function HomePage() {
  return (
    <div className="custom-scrollbar">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-emerald-900/20 via-transparent to-transparent" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent" />

        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }} />

        <div className="relative px-6 py-20 md:py-28 text-center">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/30 glow-emerald">
              <Shield className="h-7 w-7 text-emerald-400" />
            </div>
          </div>

          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-4">
            <span className="text-white">Grid</span>
            <span className="text-emerald-400">Guardian</span>
          </h1>

          <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-3 leading-relaxed">
            Autonomous Multi-Agent Disaster Response Platform
          </p>
          <p className="text-sm text-slate-500 max-w-xl mx-auto mb-10">
            AI-powered coordination of emergency triage, resource allocation, public alerting,
            and logistics -- all orchestrated through an intelligent agent network.
          </p>

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 text-white font-semibold text-sm hover:bg-emerald-500 transition-all duration-200 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30"
            >
              Open Dashboard
              <ChevronRight className="h-4 w-4" />
            </Link>
            <Link
              href="/settings"
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800 text-slate-300 font-medium text-sm border border-slate-700/50 hover:bg-slate-700/80 hover:text-white transition-all duration-200"
            >
              <Radio className="h-4 w-4" />
              Settings
            </Link>
          </div>
        </div>
      </section>

      {/* Agent Architecture */}
      <section className="px-6 py-12">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold text-white mb-2">Agent Architecture</h2>
          <p className="text-sm text-slate-400">
            Five specialized AI agents working in concert for rapid disaster response
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 max-w-6xl mx-auto">
          {AGENTS.map((agent) => {
            const c = colorMap[agent.color];
            return (
              <div
                key={agent.name}
                className={`group relative rounded-xl border ${c.border} ${c.bg} p-4 transition-all duration-300 hover:shadow-xl ${c.glow}`}
              >
                <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none" />
                <div className="relative">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${c.bg} border ${c.border} mb-3`}>
                    <agent.icon className={`h-4.5 w-4.5 ${c.text}`} />
                  </div>
                  <h3 className="text-sm font-semibold text-white mb-1">{agent.name}</h3>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{agent.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Connection lines (decorative) */}
        <div className="flex justify-center mt-6">
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-slate-800/40 border border-slate-700/30">
            <Network className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-[11px] text-slate-400">A2A Protocol</span>
            <span className="text-[11px] text-slate-600">|</span>
            <Cpu className="h-3.5 w-3.5 text-blue-400" />
            <span className="text-[11px] text-slate-400">MCP Tools</span>
            <span className="text-[11px] text-slate-600">|</span>
            <Users className="h-3.5 w-3.5 text-amber-400" />
            <span className="text-[11px] text-slate-400">Human-in-the-Loop</span>
          </div>
        </div>
      </section>

      {/* Demo Scenarios */}
      <section className="px-6 py-12 pb-20">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold text-white mb-2">Launch a Simulation</h2>
          <p className="text-sm text-slate-400">
            Choose a disaster scenario to see the agents in action
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <DemoScenarios />
        </div>
      </section>
    </div>
  );
}
