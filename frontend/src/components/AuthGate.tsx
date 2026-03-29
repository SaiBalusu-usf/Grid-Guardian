'use client';

import { useState, useEffect, useCallback } from 'react';
import { Shield, KeyRound, LogIn } from 'lucide-react';

interface AuthGateProps {
  children: React.ReactNode;
}

export default function AuthGate({ children }: AuthGateProps) {
  const [hasKey, setHasKey] = useState<boolean>(true); // default true to avoid flash
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');

  const checkKey = useCallback(() => {
    const key = localStorage.getItem('gridguardian_api_key');
    setHasKey(!!key);
  }, []);

  useEffect(() => {
    checkKey();
    const handleAuthRequired = () => {
      setHasKey(false);
      setError('Session expired or invalid API key. Please re-enter.');
    };
    window.addEventListener('auth_required', handleAuthRequired);
    return () => window.removeEventListener('auth_required', handleAuthRequired);
  }, [checkKey]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = apiKey.trim();
    if (!trimmed) {
      setError('Please enter an API key');
      return;
    }
    localStorage.setItem('gridguardian_api_key', trimmed);
    setHasKey(true);
    setError('');
    setApiKey('');
  };

  const handleSkip = () => {
    localStorage.setItem('gridguardian_api_key', 'dev_skip');
    setHasKey(true);
    setError('');
    setApiKey('');
  };

  if (hasKey) {
    return <>{children}</>;
  }

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-950/90 backdrop-blur-sm">
      <div className="w-full max-w-sm mx-4 rounded-2xl border border-slate-700/50 bg-slate-900 p-8 shadow-2xl animate-scale-in">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-emerald-500/15 border border-emerald-500/30 mb-4">
            <Shield className="h-7 w-7 text-emerald-400" />
          </div>
          <h2 className="text-xl font-bold text-white">GridGuardian Access</h2>
          <p className="text-sm text-slate-400 mt-1">Enter your API key to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <div className="relative">
              <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="password"
                value={apiKey}
                onChange={(e) => { setApiKey(e.target.value); setError(''); }}
                placeholder="gg_..."
                className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700/50 text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-colors"
                autoFocus
              />
            </div>
            {error && (
              <p className="mt-2 text-xs text-red-400">{error}</p>
            )}
          </div>

          <button
            type="submit"
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
          >
            <LogIn className="h-4 w-4" />
            Authenticate
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={handleSkip}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            Skip (dev mode)
          </button>
        </div>
      </div>
    </div>
  );
}
