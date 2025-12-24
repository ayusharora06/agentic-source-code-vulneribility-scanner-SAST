'use client';

import { useState, useEffect } from 'react';
import { FileText, ArrowLeft, Shield, Wrench, X, Bug, Terminal, BarChart3 } from 'lucide-react';
import Link from 'next/link';

interface Report {
  session_id: string;
  status: string;
  target: string;
  analysis_type?: string;
  started_at: number;
  completed_at?: number;
  vulnerabilities: any[];
  triage_results: any[];
  patches: any[];
  povs: any[];
  debug_sessions: any[];
  coverage_analysis: any;
  flip_inputs?: any[];
  input_formats?: any[];
  coverage_gaps?: any[];
  summary: any;
  cost: number;
  errors: string[];
}

export default function ReportsPage() {
  const [reports, setReports] = useState<string[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await fetch('/api/v1/reports');
      const data = await response.json();
      setReports(data.reports || []);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReportDetails = async (name: string) => {
    setLoadingReport(true);
    try {
      const response = await fetch(`/api/v1/reports/${name}`);
      const data: Report = await response.json();
      setSelectedReport(data);
    } catch (error) {
      console.error('Failed to fetch report:', error);
    } finally {
      setLoadingReport(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-blue-100 text-blue-800 border-blue-200',
    };
    return colors[severity] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="min-h-screen bg-theme-bg-secondary p-6">
      <div className="max-w-7xl mx-auto">
        <Link href="/" className="inline-flex items-center text-theme-text-secondary hover:text-theme-primary mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <div className="card">
              <h2 className="text-lg font-bold text-theme-text-primary mb-4">Reports</h2>
              {loading ? (
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-theme-primary mx-auto"></div>
              ) : reports.length === 0 ? (
                <p className="text-theme-text-secondary text-sm text-center py-4">No reports yet</p>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {reports.map((name) => (
                    <button
                      key={name}
                      onClick={() => fetchReportDetails(name)}
                      className={`w-full text-left p-3 rounded-lg border text-sm font-mono transition-colors ${
                        selectedReport?.session_id === name
                          ? 'border-theme-primary bg-blue-50'
                          : 'border-theme-border hover:border-theme-primary'
                      }`}
                    >
                      {name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-3">
            {loadingReport ? (
              <div className="card text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-theme-primary mx-auto"></div>
              </div>
            ) : selectedReport ? (
              <div className="space-y-6">
                <div className="card">
                  <div className="flex justify-between items-start mb-4">
                    <h2 className="text-xl font-bold text-theme-text-primary">{selectedReport.session_id}</h2>
                    <button onClick={() => setSelectedReport(null)} className="text-theme-text-secondary hover:text-theme-text-primary">
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-theme-text-secondary">Status</p>
                      <p className="font-medium">{selectedReport.status}</p>
                    </div>
                    <div>
                      <p className="text-xs text-theme-text-secondary">Vulnerabilities</p>
                      <p className="text-lg font-bold text-red-600">{selectedReport.vulnerabilities?.length || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-theme-text-secondary">Patches</p>
                      <p className="text-lg font-bold text-green-600">{selectedReport.patches?.length || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-theme-text-secondary">POCs</p>
                      <p className="text-lg font-bold text-purple-600">{selectedReport.povs?.length || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-theme-text-secondary">Cost</p>
                      <p className="font-bold">${(selectedReport.cost || 0).toFixed(4)}</p>
                    </div>
                  </div>
                  
                  <p className="text-xs text-theme-text-secondary">Target</p>
                  <p className="text-sm font-mono break-all">{selectedReport.target}</p>
                </div>

                {selectedReport.vulnerabilities?.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                      <Shield className="h-5 w-5" /> Vulnerabilities
                    </h3>
                    <div className="space-y-4">
                      {selectedReport.vulnerabilities.map((vuln: any) => {
                        const triage = selectedReport.triage_results?.find((t: any) => t.vulnerability_id === vuln.vuln_id);
                        const patch = selectedReport.patches?.find((p: any) => p.vulnerability_id === vuln.vuln_id);
                        
                        return (
                          <div key={vuln.vuln_id} className={`p-4 rounded-lg border ${getSeverityColor(vuln.severity)}`}>
                            <div className="flex justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{vuln.vuln_type}</span>
                                {vuln.in_diff !== undefined && (
                                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                    vuln.in_diff 
                                      ? 'bg-red-100 text-red-700 border border-red-300' 
                                      : 'bg-yellow-100 text-yellow-700 border border-yellow-300'
                                  }`}>
                                    {vuln.in_diff ? 'In Commit' : 'Pre-existing'}
                                  </span>
                                )}
                              </div>
                              <span className="text-xs uppercase font-bold">{vuln.severity}</span>
                            </div>
                            <p className="text-sm mb-2">{vuln.description}</p>
                            <p className="text-xs text-gray-600 mb-2">{vuln.file_path}:{vuln.line_number}</p>
                            
                            {vuln.code_snippet && (
                              <pre className="bg-gray-900 text-gray-100 p-2 rounded text-xs overflow-x-auto mb-2">{vuln.code_snippet}</pre>
                            )}
                            
                            {triage && (
                              <div className="mt-2 p-2 bg-white/50 rounded text-xs">
                                <strong>Priority:</strong> {triage.priority} | <strong>CVSS:</strong> {triage.cvss_estimate}
                              </div>
                            )}
                            
                            {patch && (
                              <div className="mt-2 p-2 bg-green-50 rounded text-xs border border-green-200">
                                <p className="font-medium text-green-800 flex items-center gap-1">
                                  <Wrench className="h-3 w-3" /> Patch ({(patch.confidence * 100).toFixed(0)}%)
                                </p>
                                <pre className="bg-gray-900 text-green-400 p-2 rounded mt-1 overflow-x-auto">{patch.patched_code}</pre>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {selectedReport.povs?.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                      <Bug className="h-5 w-5" /> Proof of Concepts
                    </h3>
                    <div className="space-y-4">
                      {selectedReport.povs.map((pov: any, i: number) => (
                        <div key={i} className="p-4 rounded-lg border border-purple-200 bg-purple-50">
                          <div className="flex justify-between mb-2">
                            <span className="font-medium">{pov.exploit_type}</span>
                            <span className="text-xs uppercase font-bold text-purple-700">{pov.risk_level}</span>
                          </div>
                          <p className="text-sm mb-2">{pov.description}</p>
                          {pov.payload && (
                            <pre className="bg-gray-900 text-purple-400 p-2 rounded text-xs overflow-x-auto mb-2">{pov.payload}</pre>
                          )}
                          {pov.preconditions?.length > 0 && (
                            <div className="text-xs text-gray-600">
                              <strong>Preconditions:</strong> {pov.preconditions.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedReport.debug_sessions?.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                      <Terminal className="h-5 w-5" /> Debug Sessions
                    </h3>
                    <div className="space-y-4">
                      {selectedReport.debug_sessions.map((session: any, i: number) => (
                        <div key={i} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
                          <p className="text-sm mb-2">{session.analysis}</p>
                          {session.breakpoints?.length > 0 && (
                            <div className="mb-2">
                              <p className="text-xs font-medium mb-1">Breakpoints:</p>
                              {session.breakpoints.map((bp: any, j: number) => (
                                <code key={j} className="block text-xs bg-gray-200 p-1 rounded mb-1">
                                  {bp.file_path}:{bp.line_number} {bp.condition && `if ${bp.condition}`}
                                </code>
                              ))}
                            </div>
                          )}
                          {session.actions?.length > 0 && (
                            <div>
                              <p className="text-xs font-medium mb-1">Commands:</p>
                              {session.actions.map((action: any, j: number) => (
                                <code key={j} className="block text-xs bg-gray-900 text-green-400 p-1 rounded mb-1">
                                  {action.command}
                                </code>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedReport.coverage_analysis?.gaps?.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                      <BarChart3 className="h-5 w-5" /> Coverage Analysis
                    </h3>
                    <div className="mb-4">
                      <p className="text-sm">Coverage: {(selectedReport.coverage_analysis.coverage_pct * 100).toFixed(1)}%</p>
                    </div>
                    <div className="space-y-2">
                      {selectedReport.coverage_analysis.gaps.slice(0, 10).map((gap: any, i: number) => (
                        <div key={i} className="p-2 rounded border border-yellow-200 bg-yellow-50 text-sm">
                          <span className="font-medium">Lines {gap.start_line}-{gap.end_line}</span>
                          <span className="text-xs ml-2 text-yellow-700">{gap.gap_type}</span>
                          <p className="text-xs text-gray-600">{gap.suggestion}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedReport.flip_inputs?.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-bold mb-4">Generated Fuzzing Inputs</h3>
                    <div className="space-y-2">
                      {selectedReport.flip_inputs.map((input: any, i: number) => (
                        <div key={i} className="p-2 rounded border bg-gray-50 text-sm">
                          <p className="font-medium">{input.strategy}</p>
                          <code className="text-xs bg-gray-200 p-1 rounded block mt-1">{input.input_hex}</code>
                          <p className="text-xs text-gray-600 mt-1">{input.input_description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedReport.errors?.length > 0 && (
                  <div className="card bg-red-50 border-red-200">
                    <h3 className="font-bold text-red-800 mb-2">Errors</h3>
                    {selectedReport.errors.map((e, i) => <p key={i} className="text-sm text-red-700">{e}</p>)}
                  </div>
                )}
              </div>
            ) : (
              <div className="card text-center py-12">
                <FileText className="h-12 w-12 mx-auto text-theme-text-secondary mb-4" />
                <p className="text-theme-text-secondary">Select a report to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
