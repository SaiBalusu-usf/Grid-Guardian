import type { Metadata } from 'next';
import './globals.css';
import StreamingProvider from '@/components/StreamingProvider';
import AuthGate from '@/components/AuthGate';
import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'GridGuardian - Autonomous Disaster Response',
  description:
    'Multi-agent AI operations dashboard for autonomous disaster response coordination, resource allocation, and public alerting.',
  keywords: ['disaster response', 'AI agents', 'operations dashboard', 'emergency management'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🛡️</text></svg>" />
      </head>
      <body className="min-h-screen bg-slate-950 text-white antialiased">
        <StreamingProvider>
          <AuthGate>
            <Navbar />
            <main className="mx-auto max-w-screen-2xl">{children}</main>
          </AuthGate>
        </StreamingProvider>
      </body>
    </html>
  );
}
