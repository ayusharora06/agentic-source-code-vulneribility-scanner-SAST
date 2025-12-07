'use client';

import { useState, useEffect } from 'react';
import { Shield, FileSearch, Settings } from 'lucide-react';
import Link from 'next/link';

import { AgentStatus } from '@/components/AgentStatus';
import { QuickActions } from '@/components/QuickActions';
import { StatsOverview } from '@/components/StatsOverview';
import { useDashboard } from '@/hooks/useDashboard';

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const { stats, agents, isConnected, loading, rebuilding, rebuildStats } = useDashboard(60000);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen bg-theme-bg-secondary">
      <header className="bg-gradient-to-r from-theme-primary to-theme-primary-light shadow-lg border-b-2 border-theme-primary-dark">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center space-x-4">
              <Shield className="h-8 w-8 text-white" />
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Agentic Ethical Hacker
                </h1>
                <p className="text-blue-100">
                  AI-Powered Vulnerability Analysis
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  isConnected ? 'bg-green-400' : 'bg-red-400'
                }`} />
                <span className="text-sm text-white">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              <nav className="flex items-center space-x-4">
                <Link 
                  href="/analysis/upload" 
                  className="text-white hover:text-blue-100 transition-colors"
                >
                  <FileSearch className="h-5 w-5" />
                </Link>
                <Link 
                  href="/settings" 
                  className="text-white hover:text-blue-100 transition-colors"
                >
                  <Settings className="h-5 w-5" />
                </Link>
              </nav>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          <StatsOverview stats={stats} loading={loading} rebuilding={rebuilding} onRebuild={rebuildStats} />
          <QuickActions />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <AgentStatus isConnected={isConnected} agents={agents} />
          </div>
        </div>
      </main>
    </div>
  );
}

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-theme-bg-secondary flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-theme-primary mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-theme-text-primary">
          Loading Dashboard
        </h2>
        <p className="text-theme-text-secondary mt-2">
          Initializing vulnerability analysis system...
        </p>
      </div>
    </div>
  );
}
