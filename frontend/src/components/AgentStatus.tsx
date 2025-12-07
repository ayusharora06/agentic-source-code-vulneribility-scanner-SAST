'use client';

import { Bot, CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface AgentInfo {
  agent_id: string;
  model: string;
  temperature: number;
  status: string;
  available_tools: number;
}

interface AgentStatusProps {
  isConnected: boolean;
  agents: Record<string, AgentInfo>;
}

export function AgentStatus({ isConnected, agents }: AgentStatusProps) {

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Bot className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-blue-600 bg-blue-50';
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-theme-text-primary">
          Agent Status
        </h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-400' : 'bg-red-400'
          }`} />
          <span className="text-sm text-theme-text-secondary">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {Object.keys(agents).length === 0 ? (
        <div className="text-center py-8">
          <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-theme-text-secondary">No agents available</p>
        </div>
      ) : (
        <div className="space-y-3">
          {Object.entries(agents).map(([agentId, agent]) => (
            <div
              key={agentId}
              className="flex items-center justify-between p-3 rounded-lg border border-theme-border hover:border-theme-primary transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-theme-bg-tertiary">
                  <Bot className="h-4 w-4 text-theme-primary" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-theme-text-primary">
                    {agent.agent_id.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  </h4>
                  <p className="text-xs text-theme-text-secondary">
                    {agent.model} • {agent.available_tools} tools
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {getStatusIcon(agent.status)}
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                  {agent.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-theme-border">
        <div className="text-xs text-theme-text-secondary">
          <p>Agents automatically handle vulnerability analysis, patch generation, and triage.</p>
        </div>
      </div>
    </div>
  );
}