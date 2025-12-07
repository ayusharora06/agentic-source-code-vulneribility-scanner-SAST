'use client';

import { useState } from 'react';
import { Upload, FileText, Code, FolderOpen, Play, GitBranch, Binary } from 'lucide-react';
import Link from 'next/link';

export function QuickActions() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const startQuickAnalysis = async (type: string) => {
    setIsAnalyzing(true);
    
    try {
      // This would trigger a quick analysis
      await new Promise(resolve => setTimeout(resolve, 2000));
      console.log(`Starting ${type} analysis`);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const actions = [
    {
      name: 'Upload File',
      description: 'Upload and analyze a source code file',
      icon: Upload,
      color: 'bg-blue-500 hover:bg-blue-600',
      action: () => startQuickAnalysis('file'),
      href: '/analysis/upload',
    },
    {
      name: 'Analyze Project',
      description: 'Scan an entire project directory',
      icon: FolderOpen,
      color: 'bg-green-500 hover:bg-green-600',
      action: () => startQuickAnalysis('project'),
      href: '/analysis/project',
    },
    {
      name: 'Code Review',
      description: 'Paste code for instant analysis',
      icon: Code,
      color: 'bg-purple-500 hover:bg-purple-600',
      action: () => startQuickAnalysis('code'),
      href: '/analysis/code',
    },
    {
      name: 'Diff Analysis',
      description: 'Analyze git diffs for security issues',
      icon: GitBranch,
      color: 'bg-yellow-500 hover:bg-yellow-600',
      action: () => startQuickAnalysis('diff'),
      href: '/analysis/diff',
    },
    {
      name: 'Corpus Analysis',
      description: 'Decode fuzzer input formats',
      icon: Binary,
      color: 'bg-pink-500 hover:bg-pink-600',
      action: () => startQuickAnalysis('corpus'),
      href: '/analysis/corpus',
    },
    {
      name: 'View Reports',
      description: 'Browse analysis reports and results',
      icon: FileText,
      color: 'bg-orange-500 hover:bg-orange-600',
      href: '/reports',
    },
  ];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-theme-text-primary">
          Quick Actions
        </h2>
        <div className="flex items-center space-x-2">
          <Play className="h-5 w-5 text-theme-primary" />
          <span className="text-sm text-theme-text-secondary">
            Start Analysis
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
        {actions.map((action) => {
          const Icon = action.icon;
          const Component = action.href ? Link : 'button';
          
          return (
            <Component
              key={action.name}
              href={action.href || '#'}
              onClick={action.action}
              disabled={isAnalyzing}
              className="group relative overflow-hidden rounded-lg border border-theme-border bg-white p-6 hover:border-theme-primary hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex flex-col items-center text-center space-y-3">
                <div className={`p-3 rounded-full ${action.color} transition-colors`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-theme-text-primary group-hover:text-theme-primary">
                    {action.name}
                  </h3>
                  <p className="text-xs text-theme-text-secondary mt-1">
                    {action.description}
                  </p>
                </div>
              </div>

              {isAnalyzing && action.action && (
                <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-theme-primary"></div>
                </div>
              )}
            </Component>
          );
        })}
      </div>

    </div>
  );
}