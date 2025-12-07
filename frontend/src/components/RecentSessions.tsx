'use client';

import { PlayCircle, CheckCircle, XCircle, Clock, MoreHorizontal } from 'lucide-react';
import Link from 'next/link';

interface Session {
  session_id: string;
  analysis_type?: string;
  target?: string;
  status: string;
  started_at?: number;
  created_at?: number;
  completed_at?: number;
  total_vulnerabilities?: number;
  vulnerabilities_count?: number;
}

interface RecentSessionsProps {
  sessions: Session[];
}

export function RecentSessions({ sessions }: RecentSessionsProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'running':
        return <PlayCircle className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'running':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatTarget = (target?: string, type?: string) => {
    if (!target) return 'Unknown';
    if (type === 'code') return 'Code Snippet';
    if (target.length > 30) {
      return '...' + target.slice(-30);
    }
    return target;
  };

  const formatDate = (timestamp?: number) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-theme-text-primary">
          Recent Sessions
        </h3>
        <Link 
          href="/reports"
          className="text-sm text-theme-primary hover:text-theme-primary-dark"
        >
          View All
        </Link>
      </div>

      {sessions.length === 0 ? (
        <div className="text-center py-8">
          <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-theme-text-secondary">No recent sessions</p>
          <Link 
            href="/analysis/upload" 
            className="btn-primary mt-4 text-sm inline-block"
          >
            Start Analysis
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <div
              key={session.session_id}
              className="flex items-center justify-between p-3 rounded-lg border border-theme-border hover:border-theme-primary transition-colors"
            >
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                {getStatusIcon(session.status)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs px-2 py-1 rounded bg-theme-bg-tertiary text-theme-text-secondary font-medium">
                      {(session.analysis_type || 'file').toUpperCase()}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded border font-medium ${getStatusColor(session.status)}`}>
                      {session.status}
                    </span>
                  </div>
                  
                  <p className="text-sm font-medium text-theme-text-primary truncate mt-1">
                    {formatTarget(session.target, session.analysis_type)}
                  </p>
                  
                  <div className="flex items-center space-x-4 text-xs text-theme-text-tertiary mt-1">
                    <span>
                      {formatDate(session.started_at || session.created_at)}
                    </span>
                    {(session.total_vulnerabilities || session.vulnerabilities_count || 0) > 0 && (
                      <span className="text-red-600">
                        {session.total_vulnerabilities || session.vulnerabilities_count} vulnerabilities
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <button className="p-1 hover:bg-theme-bg-tertiary rounded">
                <MoreHorizontal className="h-4 w-4 text-theme-text-secondary" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-theme-border">
        <div className="flex items-center justify-between text-sm">
          <span className="text-theme-text-secondary">
            {sessions.filter(s => s.status === 'active' || s.status === 'running').length} active sessions
          </span>
          <Link 
            href="/analysis/upload"
            className="text-theme-primary hover:text-theme-primary-dark font-medium"
          >
            + New Analysis
          </Link>
        </div>
      </div>
    </div>
  );
}
