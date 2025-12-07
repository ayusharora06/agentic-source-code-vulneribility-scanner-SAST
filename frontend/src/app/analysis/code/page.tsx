'use client';

import { useState, useEffect } from 'react';
import { Code, ArrowLeft, AlertCircle, CheckCircle, Play, Shield, Wrench, Clock } from 'lucide-react';
import Link from 'next/link';
import { useStatusSocket } from '@/hooks/useStatusSocket';
import langDetector from 'lang-detector';

interface StatusLog {
  time: string;
  event: string;
  message: string;
}

const SAMPLE_CODE = `// Paste your code here for security analysis
// Example vulnerable C code:

#include <stdio.h>
#include <string.h>

void vulnerable_function(char *user_input) {
    char buffer[64];
    strcpy(buffer, user_input);  // Buffer overflow vulnerability
    printf("Input: %s\\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc > 1) {
        vulnerable_function(argv[1]);
    }
    return 0;
}`;

export default function CodeReviewPage() {
  const [code, setCode] = useState('');
  const [detectedLanguage, setDetectedLanguage] = useState<string>('Unknown');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'complete' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<StatusLog[]>([]);
  const [summary, setSummary] = useState<any>(null);

  const { isConnected, lastEvent } = useStatusSocket();

  useEffect(() => {
    if (code.trim().length > 10) {
      const detected = langDetector(code);
      setDetectedLanguage(detected || 'Unknown');
    } else {
      setDetectedLanguage('Unknown');
    }
  }, [code]);

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
    if (!code.trim()) {
      setError('Please enter some code to analyze');
      setStatus('error');
      return;
    }

    setStatus('analyzing');
    setError(null);
    setLogs([]);
    setSummary(null);

    try {
      const response = await fetch('/api/v1/analysis/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'code',
          target: code,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start analysis');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setLogs([{ time: new Date().toLocaleTimeString(), event: 'started', message: 'Code analysis started' }]);
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

  const loadSampleCode = () => {
    setCode(SAMPLE_CODE);
  };

  const getEventIcon = (event: string) => {
    if (event.includes('vuln')) return <Shield className="h-4 w-4 text-red-500" />;
    if (event.includes('patch')) return <Wrench className="h-4 w-4 text-green-500" />;
    if (event.includes('triage')) return <Clock className="h-4 w-4 text-yellow-500" />;
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
          <h1 className="text-2xl font-bold text-theme-text-primary mb-2">Code Review</h1>
          <p className="text-theme-text-secondary mb-6">Paste code for instant security analysis</p>

          {status === 'idle' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-theme-text-secondary">Detected:</span>
                  <span className="px-2 py-1 bg-theme-bg-tertiary rounded text-sm font-medium text-theme-text-primary">
                    {detectedLanguage}
                  </span>
                </div>
                <button onClick={loadSampleCode} className="text-sm text-theme-primary hover:underline">
                  Load Sample Code
                </button>
              </div>

              <div className="mb-6">
                <div className="relative">
                  <Code className="absolute left-3 top-3 h-5 w-5 text-theme-text-secondary" />
                  <textarea
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="Paste your code here..."
                    rows={16}
                    className="w-full pl-10 pr-4 py-3 border border-theme-border rounded-lg bg-theme-bg-primary text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary font-mono text-sm"
                    spellCheck={false}
                  />
                </div>
                <p className="text-xs text-theme-text-secondary mt-2">
                  {code.length} characters | {code.split('\n').length} lines
                </p>
              </div>

              <button
                onClick={startAnalysis}
                disabled={!code.trim()}
                className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Play className="h-5 w-5" />
                Analyze Code
              </button>
            </div>
          )}

          {status === 'analyzing' && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-theme-primary"></div>
                <span className="text-theme-text-primary font-medium">Analyzing code...</span>
                <span className="text-theme-text-secondary text-sm">
                  {code.split('\n').length} lines of {detectedLanguage}
                </span>
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
                    <p className="text-theme-text-secondary">Vulnerabilities</p>
                  </div>
                  <div>
                    <span className="text-green-600 font-bold text-lg">{summary.patches_generated || 0}</span>
                    <p className="text-theme-text-secondary">Patches</p>
                  </div>
                </div>
              )}
              <div className="flex justify-center space-x-4">
                <button onClick={reset} className="btn-secondary">Analyze More Code</button>
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
