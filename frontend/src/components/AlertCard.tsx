'use client';

import { useState } from 'react';
import { Bell, CheckCircle, Globe, MapPin, Clock, Loader2 } from 'lucide-react';
import { cn, severityBorder, severityColor, timeAgo, formatTimestamp } from '@/lib/utils';
import { acknowledgeAlert } from '@/lib/api';
import type { Alert } from '@/lib/types';

interface AlertCardProps {
  alert: Alert;
  onAcknowledged?: (alert: Alert) => void;
}

export default function AlertCard({ alert, onAcknowledged }: AlertCardProps) {
  const [acknowledging, setAcknowledging] = useState(false);
  const [acked, setAcked] = useState(alert.status === 'acknowledged');

  async function handleAck() {
    if (acked || acknowledging) return;
    setAcknowledging(true);
    try {
      const updated = await acknowledgeAlert(alert.id);
      setAcked(true);
      onAcknowledged?.(updated);
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    } finally {
      setAcknowledging(false);
    }
  }

  return (
    <div
      className={cn(
        'rounded-xl border-l-4 border border-slate-700/50 bg-slate-800/60 p-4 transition-all duration-200 hover:bg-slate-800/80',
        severityBorder(alert.severity)
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span
              className={cn(
                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border',
                alert.severity === 'critical'
                  ? 'bg-red-500/15 text-red-400 border-red-500/30'
                  : alert.severity === 'high'
                    ? 'bg-orange-500/15 text-orange-400 border-orange-500/30'
                    : alert.severity === 'medium'
                      ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                      : 'bg-blue-500/15 text-blue-400 border-blue-500/30'
              )}
            >
              <Bell className="h-2.5 w-2.5" />
              {alert.severity}
            </span>

            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-700/50 text-[10px] font-medium text-slate-300 border border-slate-600/30">
              <Globe className="h-2.5 w-2.5" />
              {alert.language.toUpperCase()}
            </span>

            {acked && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/15 text-[10px] font-medium text-emerald-400 border border-emerald-500/30">
                <CheckCircle className="h-2.5 w-2.5" />
                Acknowledged
              </span>
            )}
          </div>

          <p className="text-sm text-slate-200 leading-relaxed">{alert.message}</p>

          <div className="flex items-center gap-4 mt-2.5 text-[10px] text-slate-500">
            <span className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {alert.region}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {alert.sent_at ? timeAgo(alert.sent_at) : 'Not sent'}
            </span>
          </div>
        </div>

        {!acked && (
          <button
            onClick={handleAck}
            disabled={acknowledging}
            className={cn(
              'shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200',
              'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
              'hover:bg-emerald-500/20 hover:border-emerald-500/50',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {acknowledging ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <CheckCircle className="h-3.5 w-3.5" />
            )}
            ACK
          </button>
        )}
      </div>
    </div>
  );
}
