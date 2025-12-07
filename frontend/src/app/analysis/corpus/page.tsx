'use client';

import { useState, useEffect } from 'react';
import { Binary, ArrowLeft, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import Link from 'next/link';
import { useStatusSocket } from '@/hooks/useStatusSocket';

interface StatusLog {
  time: string;
  event: string;
  message: string;
}

const SAMPLE_INPUTS = `48656c6c6f576f726c6400000010
48656c6c6f5465737400000008
48656c6c6f466f6f0000000c`;

export default function CorpusAnalysisPage() {
  const [inputs, setInputs] = useState('');
  const [harnessCode, setHarnessCode] = useState('');
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
    const inputLines = inputs.trim().split('\n').filter(Boolean);
    if (inputLines.length === 0) {
      setError('Please enter at least one input');
      setStatus('error');
      return;
    }

    setStatus('analyzing');
    setError(null);
    setLogs([]);
    setSummary(null);

    try {
      const response = await fetch('/api/v1/analysis/corpus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inputs: inputLines,
          harness_code: harnessCode.trim() || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start analysis');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setLogs([{ time: new Date().toLocaleTimeString(), event: 'started', message: 'Corpus analysis started' }]);
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

  const loadSample = () => {
    setInputs(SAMPLE_INPUTS);
    setHarnessCode('');
  };

  const getEventIcon = (event: string) => {
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
          <h1 className="text-2xl font-bold text-theme-text-primary mb-2">Corpus Analysis</h1>
          <p className="text-theme-text-secondary mb-6">Decode fuzzer input formats from corpus samples</p>

          {status === 'idle' && (
            <div>
              <div className="flex justify-end mb-4">
                <button onClick={loadSample} className="text-sm text-theme-primary hover:underline">
                  Load Sample
                </button>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-theme-text-primary mb-2">
                  Corpus Inputs (hex-encoded, one per line)
                </label>
                <textarea
                  value={inputs}
                  onChange={(e) => setInputs(e.target.value)}
                  placeholder="48656c6c6f576f726c6400000010&#10;48656c6c6f5465737400000008"
                  rows={6}
                  className="w-full px-4 py-3 border border-theme-border rounded-lg bg-theme-bg-primary text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary font-mono text-sm"
                  spellCheck={false}
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-theme-text-primary mb-2">
                  Harness Code (optional - helps identify field meanings)
                </label>
                <textarea
                  value={harnessCode}
                  onChange={(e) => setHarnessCode(e.target.value)}
                  placeholder="int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) { ... }"
                  rows={6}
                  className="w-full px-4 py-3 border border-theme-border rounded-lg bg-theme-bg-primary text-theme-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary font-mono text-sm"
                  spellCheck={false}
                />
              </div>

              <button
                onClick={startAnalysis}
                disabled={!inputs.trim()}
                className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Binary className="h-5 w-5" />
                Analyze Corpus
              </button>
            </div>
          )}

          {status === 'analyzing' && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-theme-primary"></div>
                <span className="text-theme-text-primary font-medium">Decoding input formats...</span>
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
                    <span className="text-blue-600 font-bold text-lg">{summary.inputs_analyzed || 0}</span>
                    <p className="text-theme-text-secondary">Inputs Analyzed</p>
                  </div>
                  <div>
                    <span className="text-green-600 font-bold text-lg">{summary.formats_decoded || 0}</span>
                    <p className="text-theme-text-secondary">Formats Decoded</p>
                  </div>
                  <div>
                    <span className="text-purple-600 font-bold text-lg">{summary.fields_found || 0}</span>
                    <p className="text-theme-text-secondary">Fields Found</p>
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
