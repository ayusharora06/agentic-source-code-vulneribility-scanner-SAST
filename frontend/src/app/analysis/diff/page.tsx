'use client';

import { useState, useEffect } from 'react';
import { GitBranch, ArrowLeft, AlertCircle, CheckCircle, Play, Shield, Clock } from 'lucide-react';
import Link from 'next/link';
import { useStatusSocket } from '@/hooks/useStatusSocket';

interface StatusLog {
  time: string;
  event: string;
  message: string;
}

const SAMPLE_DIFF = `diff --git a/auth.py b/auth.py
index 1234567..abcdefg 100644
--- a/auth.py
+++ b/auth.py
@@ -10,7 +10,7 @@ def authenticate(username, password):
     # Vulnerable: SQL Injection
-    query = f"SELECT * FROM users WHERE username='{username}'"
+    query = "SELECT * FROM users WHERE username=?"
     cursor.execute(query, (username,))
     user = cursor.fetchone()`;

export default function DiffAnalysisPage() {
  const [diff, setDiff] = useState('');
  const [commitMessage, setCommitMessage] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'complete' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<StatusLog[]>([]);
  const [summary, setSummary] = useState<any>(null);

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

    if (lastEvent.event === 'analysis_completed') {
      setStatus('complete');
      setSummary(lastEvent.data?.summary);
    } else if (lastEvent.event === 'analysis_failed') {
      setStatus('error');
      setError(lastEvent.data?.error || 'Analysis failed');
    }
  }, [lastEvent, sessionId]);

  const startAnalysis = async () => {
    if (!diff.trim()) {
      setError('Please enter a diff to analyze');
      setStatus('error');
      return;
    }

    setStatus('analyzing');
    setError(null);
    setLogs([]);
    setSummary(null);

    try {
      const response = await fetch('/api/v1/analysis/diff', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          diff: diff,
          commit_message: commitMessage,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start analysis');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setLogs([{ time: new Date().toLocaleTimeString(), event: 'started', message: 'Diff analysis started' }]);
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
  };

  const loadSampleDiff = () => {
    setDiff(SAMPLE_DIFF);
    setCommitMessage('Fix SQL injection vulnerability in auth');
  };

  const getEventIcon = (event: string) => {
    if (event.includes('vuln')) return <Shield className="h-4 w-4 text-red-500" />;
    if (event.includes('completed')) return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (event.includes('failed')) return <AlertCircle className="h-4 w-4 text-red-500" />;
    return <Clock className="h-4 w-4 text-blue-500" />;
  };

  return (
    <div className="min-h-screen bg-theme-bg-secondary p-6">
      <div className="max-w-4xl mx-auto">
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
          <h1 className="text-2xl font-bold text-theme-text-primary mb-2">Diff Analysis</h1>
          <p className="text-theme-text-secondary mb-6">Analyze git diffs and commits for security vulnerabilities</p>

          {status === 'idle' && (
            <div>
              <div className="flex justify-end mb-4">
                <button onClick={loadSampleDiff} className="text-sm text-theme-primary hover:underline">
                  Load Sample Diff
                </button>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-theme-text-primary mb-2">Commit Message (optional)</label>
                <input
                  type="text"
                  value={commitMessage}
                  onChange={(e) => setCommitMessage(e.target.value)}
                  placeholder="e.g., Fix authentication bug"
                  className="w-full px-4 py-2 border border-theme-border rounded-lg bg-theme-bg-primary text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary"
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-theme-text-primary mb-2">Diff Content</label>
                <div className="relative">
                  <GitBranch className="absolute left-3 top-3 h-5 w-5 text-theme-text-secondary" />
                  <textarea
                    value={diff}
                    onChange={(e) => setDiff(e.target.value)}
                    placeholder="Paste your git diff here..."
                    rows={14}
                    className="w-full pl-10 pr-4 py-3 border border-theme-border rounded-lg bg-theme-bg-primary text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary font-mono text-sm"
                    spellCheck={false}
                  />
                </div>
                <p className="text-xs text-theme-text-secondary mt-2">
                  {diff.split('\n').length} lines
                </p>
              </div>

              <button
                onClick={startAnalysis}
                disabled={!diff.trim()}
                className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Play className="h-5 w-5" />
                Analyze Diff
              </button>
            </div>
          )}

          {status === 'analyzing' && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-theme-primary"></div>
                <span className="text-theme-text-primary font-medium">Analyzing diff...</span>
              </div>
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
                    <p className="text-theme-text-secondary">Issues Found</p>
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
            <div className="space-y-2 max-h-64 overflow-y-auto">
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
