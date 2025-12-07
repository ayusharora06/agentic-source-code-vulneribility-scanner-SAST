'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface AgentInfo {
  agent_id: string;
  model: string;
  temperature: number;
  status: string;
  available_tools: number;
}

interface StatsData {
  total_vulnerabilities: number;
  total_reports: number;
  total_patches: number;
  by_severity: Record<string, number>;
}

interface HealthResponse {
  status: string;
  timestamp: number;
  llm: {
    configured: boolean;
    default_model: string;
    available_models: string[];
    total_cost: number;
    total_requests: number;
  };
  agents: Record<string, AgentInfo>;
  stats: StatsData;
}

export interface Stats {
  totalVulnerabilities: number;
  totalReports: number;
  totalPatches: number;
  bySeverity: Record<string, number>;
}

export function useDashboard(refreshInterval: number = 60000) {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      const response = await fetch('/health');

      if (!mountedRef.current) return;

      if (response.ok) {
        const healthData: HealthResponse = await response.json();
        setData(healthData);
        setIsConnected(true);
        setError(null);
      } else {
        setIsConnected(false);
        setError('Failed to fetch health data');
      }
    } catch (err) {
      if (mountedRef.current) {
        setIsConnected(false);
        setError('Failed to connect to server');
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  const rebuildStats = useCallback(async () => {
    setRebuilding(true);
    try {
      const response = await fetch('/api/v1/stats/rebuild', { method: 'POST' });
      if (response.ok) {
        await fetchData();
      }
    } catch (err) {
      console.error('Failed to rebuild stats:', err);
    } finally {
      setRebuilding(false);
    }
  }, [fetchData]);

  useEffect(() => {
    mountedRef.current = true;
    fetchData();

    const interval = setInterval(fetchData, refreshInterval);

    return () => {
      mountedRef.current = false;
      clearInterval(interval);
    };
  }, [fetchData, refreshInterval]);

  const stats: Stats = {
    totalVulnerabilities: data?.stats?.total_vulnerabilities || 0,
    totalReports: data?.stats?.total_reports || 0,
    totalPatches: data?.stats?.total_patches || 0,
    bySeverity: data?.stats?.by_severity || { critical: 0, high: 0, medium: 0, low: 0 },
  };

  return {
    stats,
    agents: data?.agents || {},
    llm: data?.llm || null,
    isConnected,
    loading,
    error,
    rebuilding,
    refresh: fetchData,
    rebuildStats
  };
}
