'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Shield,
  LayoutDashboard,
  Map,
  Activity,
  Bell,
  ListTodo,
  Building2,
  BarChart3,
  Settings,
  Radio,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useStreaming } from '@/lib/hooks';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/map', label: 'Map', icon: Map },
  { href: '/trace', label: 'Trace', icon: Activity },
  { href: '/alerts', label: 'Alerts', icon: Bell },
  { href: '/tasks', label: 'Tasks', icon: ListTodo },
  { href: '/shelters', label: 'Shelters', icon: Building2 },
  { href: '/metrics', label: 'Metrics', icon: BarChart3 },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export default function Navbar() {
  const pathname = usePathname();
  const { connected, incident } = useStreaming();

  const isActive = incident && incident.status !== 'resolved' && incident.status !== 'closed';

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl">
      <div className="mx-auto max-w-screen-2xl px-4">
        <div className="flex h-14 items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15 border border-emerald-500/30 group-hover:bg-emerald-500/25 transition-colors">
                <Shield className="h-4.5 w-4.5 text-emerald-400" />
              </div>
              <span className="text-lg font-bold tracking-tight">
                <span className="text-white">Grid</span>
                <span className="text-emerald-400">Guardian</span>
              </span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
                const active = pathname === href;
                return (
                  <Link
                    key={href}
                    href={href}
                    className={cn(
                      'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200',
                      active
                        ? 'bg-slate-700/60 text-white'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'h-2 w-2 rounded-full',
                  connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'
                )}
              />
              <span className="text-xs text-slate-400">
                {connected ? 'Live' : 'Offline'}
              </span>
            </div>

            {isActive && (
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/15 border border-red-500/30">
                <Radio className="h-3.5 w-3.5 text-red-400 animate-pulse" />
                <span className="text-xs font-medium text-red-400 uppercase tracking-wider">
                  Active
                </span>
              </div>
            )}

            {incident && (
              <div
                className={cn(
                  'px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border',
                  incident.severity === 'critical'
                    ? 'bg-red-500/15 text-red-400 border-red-500/30'
                    : incident.severity === 'high'
                      ? 'bg-orange-500/15 text-orange-400 border-orange-500/30'
                      : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                )}
              >
                {incident.severity}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="md:hidden border-t border-slate-700/50 overflow-x-auto">
        <div className="flex items-center gap-1 px-4 py-1.5">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors',
                  active
                    ? 'bg-slate-700/60 text-white'
                    : 'text-slate-400 hover:text-white'
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
