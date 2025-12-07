"""
Agents Module - LLM-powered vulnerability analysis agents
Inspired by RoboDuck's agent architecture
"""

from .agent_base import AgentBase, AgentStatus, AgentExecution, ToolCall
from .vuln_analyzer import VulnAnalyzerAgent, Vulnerability
from .triage_agent import TriageAgent, TriageResult, Priority
from .patch_producer import PatchProducerAgent, SecurityPatch
from .diff_analyzer import DiffAnalyzerAgent, DiffVulnerability
from .pov_producer import POVProducerAgent, ExploitPOV
from .branch_flipper import BranchFlipperAgent, FlipInput
from .harness_decoder import HarnessDecoderAgent, InputFormat
from .coverage_analyzer import CoverageAnalyzerAgent, CoverageReport
from .dynamic_debug import DynamicDebugAgent, DebugSession

__all__ = [
    'AgentBase',
    'AgentStatus',
    'AgentExecution',
    'ToolCall',
    'VulnAnalyzerAgent',
    'Vulnerability',
    'TriageAgent',
    'TriageResult',
    'Priority',
    'PatchProducerAgent',
    'SecurityPatch',
    'DiffAnalyzerAgent',
    'DiffVulnerability',
    'POVProducerAgent',
    'ExploitPOV',
    'BranchFlipperAgent',
    'FlipInput',
    'HarnessDecoderAgent',
    'InputFormat',
    'CoverageAnalyzerAgent',
    'CoverageReport',
    'DynamicDebugAgent',
    'DebugSession',
]


def create_agents():
    """Create the core analysis agents"""
    return {
        'vuln_analyzer': VulnAnalyzerAgent(),
        'triage_agent': TriageAgent(),
        'patch_producer': PatchProducerAgent(),
        'diff_analyzer': DiffAnalyzerAgent(),
        'pov_producer': POVProducerAgent(),
        'branch_flipper': BranchFlipperAgent(),
        'harness_decoder': HarnessDecoderAgent(),
        'coverage_analyzer': CoverageAnalyzerAgent(),
        'dynamic_debug': DynamicDebugAgent(),
    }
