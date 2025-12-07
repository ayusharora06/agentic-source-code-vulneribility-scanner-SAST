'use client';

import { useState, useEffect } from 'react';
import { FolderOpen, ArrowLeft, AlertCircle, CheckCircle, Play, Shield, Wrench, Clock, FileCode } from 'lucide-react';
import Link from 'next/link';
import { useStatusSocket } from '@/hooks/useStatusSocket';

interface StatusLog {
  time: string;
  event: string;
  message: string;
}

export default function ProjectPage() {
  const [projectPath, setProjectPath] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'complete' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<StatusLog[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [progress, setProgress] = useState<{ current: number; total: number } | null>(null);

  const { isConnected, lastEvent } = useStatusSocket();

  useEffect(() => {
    if (!lastEvent || !sessionId) return;
    if (lastEvent.data?.session_id !== sessionId) return;

    const time = new Date().toLocaleTimeString();
    const log: StatusLog = {
      time,
      event: lastEvent.event,
      message: lastEvent.data?.message || lastEvent.event,
    };
    setLogs((prev) => [...prev, log]);

    if (lastEvent.event === 'file_started' && lastEvent.data?.index) {
      setProgress({ current: lastEvent.data.index, total: lastEvent.data.total });
    }

    if (lastEvent.event === 'analysis_completed') {
      setStatus('complete');
      setSummary(lastEvent.data?.summary);
    } else if (lastEvent.event === 'analysis_failed') {
      setStatus('error');
      setError(lastEvent.data?.error || 'Analysis failed');
    }
  }, [lastEvent, sessionId]);

  const startAnalysis = async () => {
    if (!projectPath.trim()) {
      setError('Please enter a project path');
      setStatus('error');
      return;
    }

    setStatus('analyzing');
    setError(null);
    setLogs([]);
    setSummary(null);
    setProgress(null);

    try {
      const response = await fetch('/api/v1/analysis/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'project',
          target: projectPath.trim(),
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start analysis');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setLogs([{ time: new Date().toLocaleTimeString(), event: 'started', message: 'Project analysis started' }]);
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const reset = () => {
    setStatus('idle');
    setSessionId(null);
    setError(null);
    setLogs([]);
    setSummary(null);
    setProgress(null);
    setProjectPath('');
  };

  const getEventIcon = (event: string) => {
    if (event.includes('file')) return <FileCode className="h-4 w-4 text-blue-500" />;
    if (event.includes('vuln')) return <Shield className="h-4 w-4 text-red-500" />;
    if (event.includes('patch')) return <Wrench className="h-4 w-4 text-green-500" />;
    if (event.includes('triage')) return <Clock className="h-4 w-4 text-yellow-500" />;
    if (event.includes('completed')) return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (event.includes('failed')) return <AlertCircle className="h-4 w-4 text-red-500" />;
    if (event.includes('scanner')) return <FolderOpen className="h-4 w-4 text-purple-500" />;
    return <Clock className="h-4 w-4 text-blue-500" />;
  };

  return (
    <div className="min-h-screen bg-theme-bg-secondary p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link href="/" className="inline-flex items-center text-theme-text-secondary hover:text-theme-primary">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-xs text-theme-text-secondary">
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>

        <div className="card mb-6">
          <h1 className="text-2xl font-bold text-theme-text-primary mb-2">Analyze Project</h1>
          <p className="text-theme-text-secondary mb-6">Scan an entire project directory for security vulnerabilities</p>

          {status === 'idle' && (
            <div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-theme-text-primary mb-2">Project Path</label>
                <div className="relative">
                  <FolderOpen className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-theme-text-secondary" />
                  <input
                    type="text"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                    placeholder="/path/to/your/project"
                    className="w-full pl-10 pr-4 py-3 border border-theme-border rounded-lg bg-theme-bg-primary text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
                  />
                </div>
                <p className="text-xs text-theme-text-secondary mt-2">
                  Scans: .py, .js, .ts, .c, .cpp, .java, .go, .rs files
                </p>
              </div>
              <button
                onClick={startAnalysis}
                disabled={!projectPath.trim()}
                className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Play className="h-5 w-5" />
                Start Analysis
              </button>
            </div>
          )}

          {status === 'analyzing' && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-theme-primary"></div>
                <span className="text-theme-text-primary font-medium">Analyzing project...</span>
              </div>
              {progress && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-theme-text-secondary mb-1">
                    <span>Progress</span>
                    <span>{progress.current} / {progress.total} files</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-theme-primary h-2 rounded-full transition-all"
                      style={{ width: `${(progress.current / progress.total) * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          )}

          {status === 'complete' && (
            <div className="text-center py-6">
              <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
              <p className="text-theme-text-primary font-medium mb-2">Analysis Complete!</p>
              {summary && (
                <div className="flex justify-center gap-6 mb-4 text-sm">
                  <div>
                    <span className="text-red-600 font-bold text-lg">{summary.total_vulnerabilities || 0}</span>
                    <p className="text-theme-text-secondary">Vulnerabilities</p>
                  </div>
                  <div>
                    <span className="text-green-600 font-bold text-lg">{summary.patches_generated || 0}</span>
                    <p className="text-theme-text-secondary">Patches</p>
                  </div>
                </div>
              )}
              <div className="flex justify-center space-x-4">
                <button onClick={reset} className="btn-secondary">Analyze Another</button>
                <Link href="/reports" className="btn-primary">View Reports</Link>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center py-6">
              <AlertCircle className="h-12 w-12 mx-auto text-red-500 mb-4" />
              <p className="text-theme-text-primary font-medium mb-2">Error</p>
              <p className="text-red-500 text-sm mb-6">{error}</p>
              <button onClick={reset} className="btn-primary">Try Again</button>
            </div>
          )}
        </div>

        {logs.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-bold text-theme-text-primary mb-4">Live Status</h3>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {logs.map((log, i) => (
                <div key={i} className="flex items-start gap-3 p-2 rounded bg-theme-bg-secondary">
                  {getEventIcon(log.event)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-theme-text-primary">{log.message}</p>
                    <p className="text-xs text-theme-text-secondary">{log.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
