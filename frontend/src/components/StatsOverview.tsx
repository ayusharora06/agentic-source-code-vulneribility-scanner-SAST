'use client';

import { Shield, AlertTriangle, FileText, Wrench, RefreshCw } from 'lucide-react';
import { Stats } from '@/hooks/useDashboard';

interface StatsOverviewProps {
  stats: Stats;
  loading: boolean;
  rebuilding?: boolean;
  onRebuild?: () => void;
}

export function StatsOverview({ stats, loading, rebuilding, onRebuild }: StatsOverviewProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
              <div className="ml-4 flex-1">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-6 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const statCards = [
    {
      name: 'Total Vulnerabilities',
      value: stats.totalVulnerabilities,
      icon: AlertTriangle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      subtext: `${stats.bySeverity.critical || 0} critical, ${stats.bySeverity.high || 0} high`,
    },
    {
      name: 'Total Reports',
      value: stats.totalReports,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      subtext: 'analyses completed',
    },
    {
      name: 'Patches Generated',
      value: stats.totalPatches,
      icon: Wrench,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      subtext: 'security fixes',
    },
    {
      name: 'Agents Available',
      value: '3/3',
      icon: Shield,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      subtext: 'vuln, triage, patch',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        {onRebuild && (
          <button
            onClick={onRebuild}
            disabled={rebuilding}
            className="flex items-center gap-2 text-sm text-theme-text-secondary hover:text-theme-primary disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${rebuilding ? 'animate-spin' : ''}`} />
            {rebuilding ? 'Rebuilding...' : 'Rebuild Stats'}
          </button>
        )}
      </div>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="card hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`h-6 w-6 ${stat.color}`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-theme-text-secondary">
                    {stat.name}
                  </p>
                  <p className="text-2xl font-bold text-theme-text-primary">
                    {stat.value}
                  </p>
                  <p className="text-xs mt-1 text-theme-text-tertiary">
                    {stat.subtext}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
