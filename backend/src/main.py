"""
Main FastAPI application for Vulnerability Analysis Tool
LLM-powered multi-agent security analysis system
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .agents import (
    VulnAnalyzerAgent, TriageAgent, PatchProducerAgent, DiffAnalyzerAgent,
    POVProducerAgent, DynamicDebugAgent, CoverageAnalyzerAgent,
    BranchFlipperAgent, HarnessDecoderAgent, create_agents
)
from .llm import get_llm_config, get_client
from .analysis import parse_file, parse_code
from .services import get_status_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'analysis-reports')
STATS_FILE = os.path.join(os.path.dirname(__file__), '..', 'analysis-reports', 'stats.json')


def get_git_diff(path: str) -> Tuple[bool, Optional[str]]:
    """Check if path is in a git repo and get uncommitted diff"""
    try:
        if os.path.isfile(path):
            repo_dir = os.path.dirname(path)
            file_arg = path
        else:
            repo_dir = path
            file_arg = None
        
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False, None
        
        diff_cmd = ['git', 'diff', 'HEAD']
        if file_arg:
            diff_cmd.append(file_arg)
        
        diff_result = subprocess.run(
            diff_cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        diff_content = diff_result.stdout.strip()
        if not diff_content:
            staged_cmd = ['git', 'diff', '--cached']
            if file_arg:
                staged_cmd.append(file_arg)
            staged_result = subprocess.run(
                staged_cmd,
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            diff_content = staged_result.stdout.strip()
        
        return True, diff_content if diff_content else None
    except Exception:
        return False, None


def load_stats() -> Dict[str, Any]:
    """Load stats from file"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {
        "total_vulnerabilities": 0,
        "total_reports": 0,
        "total_patches": 0,
        "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0}
    }


def save_stats(stats: Dict[str, Any]):
    """Save stats to file"""
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)


def update_stats_from_report(report: Dict[str, Any]):
    """Update stats after analysis completes"""
    stats = load_stats()
    stats["total_reports"] += 1
    stats["total_vulnerabilities"] += len(report.get("vulnerabilities", []))
    stats["total_patches"] += len(report.get("patches", []))
    
    for vuln in report.get("vulnerabilities", []):
        severity = vuln.get("severity", "medium").lower()
        if severity in stats["by_severity"]:
            stats["by_severity"][severity] += 1
    
    save_stats(stats)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    config = get_llm_config()
    if config.has_any_key():
        logger.info(f"LLM configured with models: {config.get_available_models()}")
    else:
        logger.warning("No LLM API keys configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY")
    
    logger.info("Vulnerability Analysis Tool started")
    
    yield
    
    logger.info("Shutting down...")


app = FastAPI(
    title="Agentic Ethical Hacker",
    description="LLM-powered multi-agent vulnerability analysis system",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic Ethical Hacker - Vulnerability Analysis Tool",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check with complete status"""
    config = get_llm_config()
    client = get_client()
    stats = load_stats()
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "llm": {
            "configured": config.has_any_key(),
            "default_model": config.default_model,
            "available_models": config.get_available_models(),
            "total_cost": client.total_cost,
            "total_requests": client.total_requests
        },
        "agents": {
            "vuln_analyzer": {"agent_id": "vuln_analyzer", "status": "available", "model": "gpt-4o-mini", "available_tools": 3, "temperature": 0.1},
            "triage_agent": {"agent_id": "triage_agent", "status": "available", "model": "gpt-4o-mini", "available_tools": 1, "temperature": 0.1},
            "patch_producer": {"agent_id": "patch_producer", "status": "available", "model": "gpt-4o-mini", "available_tools": 1, "temperature": 0.2}
        },
        "stats": stats
    }


@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket endpoint for real-time status updates"""
    status_service = get_status_service()
    await status_service.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        status_service.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        status_service.disconnect(websocket)


@app.post("/api/v1/analysis/start")
async def start_analysis(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Start vulnerability analysis"""
    config = get_llm_config()
    if not config.has_any_key():
        raise HTTPException(
            status_code=503,
            detail="No LLM API keys configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY"
        )
    
    analysis_type = request.get("type", "file")
    target = request.get("target")
    session_id = request.get("session_id", f"session_{int(time.time())}")
    
    if not target:
        raise HTTPException(status_code=400, detail="Target is required")
    
    background_tasks.add_task(run_analysis_pipeline, session_id, analysis_type, target)
    
    return {
        "session_id": session_id,
        "status": "started",
        "analysis_type": analysis_type,
        "target": target
    }


async def run_analysis_pipeline(session_id: str, analysis_type: str, target: str):
    """Run the full analysis pipeline"""
    logger.info(f"Starting analysis pipeline for session {session_id}")
    status = get_status_service()
    
    report = {
        "session_id": session_id,
        "analysis_type": analysis_type,
        "target": target,
        "started_at": time.time(),
        "status": "running",
        "vulnerabilities": [],
        "triage_results": [],
        "patches": [],
        "povs": [],
        "debug_sessions": [],
        "flip_inputs": [],
        "coverage_analysis": {},
        "summary": {},
        "cost": 0.0,
        "errors": []
    }
    
    try:
        await status.emit_analysis_started(session_id, target)
        
        is_git, git_diff = get_git_diff(target) if analysis_type in ("file", "project") else (False, None)
        diff_vulnerabilities = []
        
        all_vulnerabilities = []
        files_to_analyze = []
        
        if analysis_type == "project":
            CODE_EXTENSIONS = ('.py', '.js', '.ts', '.jsx', '.tsx', '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.rs')
            
            if not os.path.isdir(target):
                raise ValueError(f"Project path is not a directory: {target}")
            
            for root, dirs, files in os.walk(target):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'venv', '__pycache__', 'dist', 'build')]
                for file in files:
                    if file.endswith(CODE_EXTENSIONS):
                        files_to_analyze.append(os.path.join(root, file))
            
            await status.emit_step(session_id, "scanner", "completed", f"Found {len(files_to_analyze)} code files", {"file_count": len(files_to_analyze)})
            logger.info(f"[{session_id}] Found {len(files_to_analyze)} files to analyze")
            
            diff_task = None
            if git_diff:
                await status.emit_step(session_id, "diff_analyzer", "started", "Analyzing git diff in parallel...")
                diff_analyzer = DiffAnalyzerAgent()
                diff_task = asyncio.create_task(diff_analyzer.analyze_diff(git_diff, target))
            
            vuln_analyzer = VulnAnalyzerAgent()
            
            for i, file_path in enumerate(files_to_analyze):
                try:
                    await status.emit(session_id, "file_started", {"file": file_path, "index": i + 1, "total": len(files_to_analyze), "message": f"Analyzing {os.path.basename(file_path)} ({i+1}/{len(files_to_analyze)})"})
                    
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    if len(code.strip()) < 10:
                        continue
                    
                    file_vulns = await vuln_analyzer.analyze_code(code, file_path)
                    all_vulnerabilities.extend(file_vulns)
                    
                    if file_vulns:
                        await status.emit(session_id, "file_completed", {"file": file_path, "vulns_found": len(file_vulns), "message": f"Found {len(file_vulns)} vulnerabilities in {os.path.basename(file_path)}"})
                        for v in file_vulns:
                            await status.emit_vulnerability_found(session_id, v.to_dict())
                except Exception as file_error:
                    logger.warning(f"[{session_id}] Error analyzing {file_path}: {file_error}")
                    continue
            
            vulnerabilities = all_vulnerabilities
            report["cost"] += vuln_analyzer.execution.total_cost if vuln_analyzer.execution else 0
            report["files_analyzed"] = len(files_to_analyze)
            
            if diff_task:
                try:
                    diff_vulnerabilities = await diff_task
                    report["cost"] += diff_analyzer.execution.total_cost if diff_analyzer.execution else 0
                    await status.emit_step(session_id, "diff_analyzer", "completed", f"Found {len(diff_vulnerabilities)} diff issues", {"count": len(diff_vulnerabilities)})
                    for dv in diff_vulnerabilities:
                        await status.emit_vulnerability_found(session_id, dv.to_dict())
                except Exception as diff_err:
                    logger.warning(f"[{session_id}] Diff analysis error: {diff_err}")
            
            vulnerabilities = all_vulnerabilities + diff_vulnerabilities
            report["vulnerabilities"] = [v.to_dict() for v in vulnerabilities]
            
            await status.emit_step(session_id, "vuln_analyzer", "completed", f"Found {len(vulnerabilities)} total vulnerabilities in {len(files_to_analyze)} files", {"count": len(vulnerabilities)})
            
        else:
            if analysis_type == "file":
                with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                file_path = target
            elif analysis_type == "code":
                code = target
                file_path = "<analyzed_code>"
            else:
                code = target
                file_path = target
            
            diff_task = None
            if git_diff and analysis_type == "file":
                await status.emit_step(session_id, "diff_analyzer", "started", "Analyzing git diff in parallel...")
                diff_analyzer = DiffAnalyzerAgent()
                diff_task = asyncio.create_task(diff_analyzer.analyze_diff(git_diff, file_path))
            
            await status.emit_step(session_id, "vuln_analyzer", "started", "Analyzing code for vulnerabilities...")
            logger.info(f"[{session_id}] Step 1: Vulnerability Analysis")
            vuln_analyzer = VulnAnalyzerAgent()
            code_vulnerabilities = await vuln_analyzer.analyze_code(code, file_path)
            
            report["cost"] += vuln_analyzer.execution.total_cost if vuln_analyzer.execution else 0
            
            for v in code_vulnerabilities:
                await status.emit_vulnerability_found(session_id, v.to_dict())
            
            if diff_task:
                try:
                    diff_vulnerabilities = await diff_task
                    report["cost"] += diff_analyzer.execution.total_cost if diff_analyzer.execution else 0
                    await status.emit_step(session_id, "diff_analyzer", "completed", f"Found {len(diff_vulnerabilities)} diff issues", {"count": len(diff_vulnerabilities)})
                    for dv in diff_vulnerabilities:
                        await status.emit_vulnerability_found(session_id, dv.to_dict())
                except Exception as diff_err:
                    logger.warning(f"[{session_id}] Diff analysis error: {diff_err}")
            
            vulnerabilities = code_vulnerabilities + diff_vulnerabilities
            report["vulnerabilities"] = [v.to_dict() for v in vulnerabilities]
            
            await status.emit_step(session_id, "vuln_analyzer", "completed", f"Found {len(vulnerabilities)} vulnerabilities", {"count": len(vulnerabilities)})
            logger.info(f"[{session_id}] Found {len(vulnerabilities)} vulnerabilities")
        
        if vulnerabilities:
            await status.emit_step(session_id, "triage_agent", "started", "Triaging vulnerabilities...")
            logger.info(f"[{session_id}] Step 2: Triage")
            triage_agent = TriageAgent()
            triage_results = await triage_agent.triage_vulnerabilities(
                [v.to_dict() for v in vulnerabilities]
            )
            
            report["triage_results"] = [t.to_dict() for t in triage_results]
            report["cost"] += triage_agent.execution.total_cost if triage_agent.execution else 0
            
            high_priority = [t for t in triage_results if t.priority.value in ["critical", "high"]]
            await status.emit_step(session_id, "triage_agent", "completed", f"{len(high_priority)} high priority vulnerabilities", {"high_priority": len(high_priority)})
            logger.info(f"[{session_id}] {len(high_priority)} high priority vulnerabilities")
            
            if high_priority:
                await status.emit_step(session_id, "patch_producer", "started", "Generating patches for high priority vulnerabilities...")
                logger.info(f"[{session_id}] Step 3: Patch Generation")
                patch_producer = PatchProducerAgent()
                
                high_priority_vulns = [
                    v.to_dict() for v in vulnerabilities 
                    if any(t.vulnerability_id == v.vuln_id and t.priority.value in ["critical", "high"] 
                           for t in triage_results)
                ]
                
                patches = await patch_producer.generate_patches(high_priority_vulns)
                report["patches"] = [p.to_dict() for p in patches]
                report["cost"] += patch_producer.execution.total_cost if patch_producer.execution else 0
                
                await status.emit_step(session_id, "patch_producer", "completed", f"Generated {len(patches)} patches", {"count": len(patches)})
                logger.info(f"[{session_id}] Generated {len(patches)} patches")
                
                await status.emit_step(session_id, "pov_producer", "started", "Generating proof-of-concept exploits...")
                logger.info(f"[{session_id}] Step 4: POV Generation")
                pov_producer = POVProducerAgent()
                
                all_povs = []
                for vuln in high_priority_vulns:
                    try:
                        povs = await pov_producer.generate_pov(vuln)
                        all_povs.extend([p.to_dict() for p in povs])
                    except Exception as pov_error:
                        logger.warning(f"[{session_id}] POV generation error for {vuln.get('vuln_id')}: {pov_error}")
                
                report["povs"] = all_povs
                report["cost"] += pov_producer.execution.total_cost if pov_producer.execution else 0
                
                await status.emit_step(session_id, "pov_producer", "completed", f"Generated {len(all_povs)} POCs", {"count": len(all_povs)})
                logger.info(f"[{session_id}] Generated {len(all_povs)} POCs")
                
                await status.emit_step(session_id, "dynamic_debug", "started", "Creating debug sessions...")
                logger.info(f"[{session_id}] Step 5: Debug Session Planning")
                dynamic_debug = DynamicDebugAgent()
                
                all_debug_sessions = []
                for vuln in high_priority_vulns:
                    try:
                        debug_session = await dynamic_debug.plan_debug_session(vuln, code if 'code' in dir() else "")
                        if debug_session:
                            all_debug_sessions.append(debug_session.to_dict())
                    except Exception as debug_error:
                        logger.warning(f"[{session_id}] Debug session error for {vuln.get('vuln_id')}: {debug_error}")
                
                report["debug_sessions"] = all_debug_sessions
                report["cost"] += dynamic_debug.execution.total_cost if dynamic_debug.execution else 0
                
                await status.emit_step(session_id, "dynamic_debug", "completed", f"Created {len(all_debug_sessions)} debug sessions", {"count": len(all_debug_sessions)})
                logger.info(f"[{session_id}] Created {len(all_debug_sessions)} debug sessions")
                
                await status.emit_step(session_id, "branch_flipper", "started", "Generating targeted fuzzing inputs...")
                logger.info(f"[{session_id}] Step 6: Fuzzing Input Generation")
                branch_flipper = BranchFlipperAgent()
                
                all_flip_inputs = []
                for vuln in high_priority_vulns[:5]:
                    try:
                        vuln_context = {
                            "branch_id": vuln.get("vuln_id"),
                            "line_number": vuln.get("line_number"),
                            "condition": vuln.get("vuln_type"),
                            "vulnerability": vuln.get("description"),
                            "current_value": False,
                            "target_value": True
                        }
                        source = code if 'code' in dir() else vuln.get("code_snippet", "")
                        flip_inputs = await branch_flipper.generate_flip_input(vuln_context, source, [])
                        all_flip_inputs.extend([f.to_dict() for f in flip_inputs])
                    except Exception as flip_err:
                        logger.warning(f"[{session_id}] Flip input error for {vuln.get('vuln_id')}: {flip_err}")
                
                report["flip_inputs"] = all_flip_inputs
                report["cost"] += branch_flipper.execution.total_cost if branch_flipper.execution else 0
                
                await status.emit_step(session_id, "branch_flipper", "completed", f"Generated {len(all_flip_inputs)} fuzzing inputs", {"count": len(all_flip_inputs)})
                logger.info(f"[{session_id}] Generated {len(all_flip_inputs)} fuzzing inputs")
        
        if analysis_type != "project" and 'code' in dir() and code:
            await status.emit_step(session_id, "coverage_analyzer", "started", "Analyzing code coverage gaps...")
            logger.info(f"[{session_id}] Step 7: Coverage Analysis")
            coverage_analyzer = CoverageAnalyzerAgent()
            
            try:
                coverage_data = {
                    "file_path": file_path if 'file_path' in dir() else "<code>",
                    "total_lines": len(code.split('\n')),
                    "covered_lines": 0,
                    "coverage_pct": 0.0
                }
                coverage_report = await coverage_analyzer.analyze_coverage(coverage_data, code)
                if coverage_report:
                    report["coverage_analysis"] = coverage_report.to_dict()
                report["cost"] += coverage_analyzer.execution.total_cost if coverage_analyzer.execution else 0
                
                await status.emit_step(session_id, "coverage_analyzer", "completed", "Coverage analysis complete", {})
                logger.info(f"[{session_id}] Coverage analysis complete")
            except Exception as cov_error:
                logger.warning(f"[{session_id}] Coverage analysis error: {cov_error}")
        
        report["summary"] = {
            "total_vulnerabilities": len(vulnerabilities),
            "by_severity": {},
            "high_priority_count": len([t for t in report.get("triage_results", []) 
                                        if t.get("priority") in ["critical", "high"]]),
            "patches_generated": len(report.get("patches", [])),
            "povs_generated": len(report.get("povs", [])),
            "debug_sessions": len(report.get("debug_sessions", [])),
            "fuzzing_inputs": len(report.get("flip_inputs", []))
        }
        
        for vuln in vulnerabilities:
            severity = vuln.severity
            report["summary"]["by_severity"][severity] = \
                report["summary"]["by_severity"].get(severity, 0) + 1
        
        report["status"] = "completed"
        await status.emit_analysis_completed(session_id, report["summary"])
        report["completed_at"] = time.time()
        
    except Exception as e:
        logger.error(f"[{session_id}] Analysis error: {e}")
        report["status"] = "failed"
        report["errors"].append(str(e))
        report["completed_at"] = time.time()
        await status.emit_analysis_failed(session_id, str(e))
    
    report_path = os.path.join(REPORTS_DIR, f"{session_id}.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    if report["status"] == "completed":
        update_stats_from_report(report)
    
    logger.info(f"[{session_id}] Analysis complete. Report saved to {report_path}")


@app.get("/api/v1/analysis/{session_id}/status")
async def get_analysis_status(session_id: str):
    """Get analysis status"""
    report_path = os.path.join(REPORTS_DIR, f"{session_id}.json")
    
    if not os.path.exists(report_path):
        return {
            "session_id": session_id,
            "status": "running",
            "message": "Analysis in progress..."
        }
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    return report


@app.get("/api/v1/reports")
async def list_reports():
    """List all report filenames"""
    if not os.path.exists(REPORTS_DIR):
        return {"reports": []}
    
    reports = [f.replace('.json', '') for f in os.listdir(REPORTS_DIR) if f.endswith('.json')]
    reports.sort(reverse=True)
    
    return {"reports": reports}


@app.get("/api/v1/reports/{report_name}")
async def get_report(report_name: str):
    """Get full report content"""
    report_path = os.path.join(REPORTS_DIR, f"{report_name}.json")
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    with open(report_path, 'r') as f:
        return json.load(f)


@app.get("/api/v1/stats")
async def get_stats():
    """Get aggregate stats"""
    return load_stats()


@app.post("/api/v1/stats/rebuild")
async def rebuild_stats():
    """Rebuild stats by reading all reports"""
    stats = {
        "total_vulnerabilities": 0,
        "total_reports": 0,
        "total_patches": 0,
        "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0}
    }
    
    if not os.path.exists(REPORTS_DIR):
        save_stats(stats)
        return {"message": "Stats rebuilt", "stats": stats}
    
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith('.json') and filename != 'stats.json':
            report_path = os.path.join(REPORTS_DIR, filename)
            try:
                with open(report_path, 'r') as f:
                    report = json.load(f)
                
                if report.get("status") == "completed":
                    stats["total_reports"] += 1
                    stats["total_vulnerabilities"] += len(report.get("vulnerabilities", []))
                    stats["total_patches"] += len(report.get("patches", []))
                    
                    for vuln in report.get("vulnerabilities", []):
                        severity = vuln.get("severity", "medium").lower()
                        if severity in stats["by_severity"]:
                            stats["by_severity"][severity] += 1
            except Exception as e:
                logger.warning(f"Error reading report {filename}: {e}")
    
    save_stats(stats)
    return {"message": "Stats rebuilt", "stats": stats}


def get_commit_diff(project_path: str, commit_id: str, compare_to: str = None) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, str]], Optional[List[int]]]:
    """Get diff, commit message, full file contents, and changed line numbers"""
    try:
        if not os.path.isdir(project_path):
            return None, None, None, None
        
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None, None, None, None
        
        if compare_to:
            diff_cmd = ['git', 'diff', compare_to, commit_id]
            files_cmd = ['git', 'diff', '--name-only', compare_to, commit_id]
        else:
            diff_cmd = ['git', 'show', commit_id, '--format=', '--patch']
            files_cmd = ['git', 'show', commit_id, '--format=', '--name-only']
        
        diff_result = subprocess.run(
            diff_cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        diff_content = diff_result.stdout.strip()
        
        msg_result = subprocess.run(
            ['git', 'log', '-1', '--format=%B', commit_id],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        commit_message = msg_result.stdout.strip()
        
        files_result = subprocess.run(
            files_cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        changed_files = [f.strip() for f in files_result.stdout.strip().split('\n') if f.strip()]
        
        file_contents = {}
        for file_path in changed_files[:20]:
            full_path = os.path.join(project_path, file_path)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_contents[file_path] = f.read()
                except Exception:
                    pass
        
        changed_lines = parse_diff_line_numbers(diff_content)
        
        return diff_content, commit_message, file_contents, changed_lines
    except Exception:
        return None, None, None, None


def parse_diff_line_numbers(diff_content: str) -> Dict[str, List[int]]:
    """Extract changed line numbers from diff content"""
    import re
    changed_lines = {}
    current_file = None
    current_line = 0
    
    for line in diff_content.split('\n'):
        if line.startswith('+++ b/'):
            current_file = line[6:]
            changed_lines[current_file] = []
        elif line.startswith('@@ '):
            match = re.search(r'\+(\d+)', line)
            if match:
                current_line = int(match.group(1))
        elif current_file and line.startswith('+') and not line.startswith('+++'):
            changed_lines[current_file].append(current_line)
            current_line += 1
        elif current_file and not line.startswith('-'):
            current_line += 1
    
    return changed_lines


@app.post("/api/v1/analysis/diff")
async def analyze_diff(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Analyze a git commit for security issues"""
    config = get_llm_config()
    if not config.has_any_key():
        raise HTTPException(
            status_code=503,
            detail="No LLM API keys configured"
        )
    
    project_path = request.get("project_path")
    commit_id = request.get("commit_id")
    compare_to = request.get("compare_to")
    session_id = request.get("session_id", f"diff_{int(time.time())}")
    
    if not project_path or not commit_id:
        raise HTTPException(status_code=400, detail="project_path and commit_id are required")
    
    if not os.path.isdir(project_path):
        raise HTTPException(status_code=400, detail="Invalid project path")
    
    diff_content, commit_message, file_contents, changed_lines = get_commit_diff(project_path, commit_id, compare_to)
    
    if not diff_content:
        raise HTTPException(status_code=400, detail="Could not get diff for commit. Check project path and commit ID.")
    
    background_tasks.add_task(run_diff_analysis, session_id, diff_content, project_path, commit_message, commit_id, file_contents, changed_lines)
    
    return {
        "session_id": session_id,
        "status": "started",
        "analysis_type": "diff",
        "commit_id": commit_id
    }


async def run_diff_analysis(session_id: str, diff_content: str, project_path: str, commit_message: str, commit_id: str = "", file_contents: Dict[str, str] = None, changed_lines: Dict[str, List[int]] = None):
    """Run diff analysis pipeline"""
    logger.info(f"Starting diff analysis for session {session_id}")
    status = get_status_service()
    file_contents = file_contents or {}
    changed_lines = changed_lines or {}
    
    report = {
        "session_id": session_id,
        "analysis_type": "diff",
        "project_path": project_path,
        "commit_id": commit_id,
        "commit_message": commit_message,
        "started_at": time.time(),
        "status": "running",
        "vulnerabilities": [],
        "summary": {},
        "cost": 0.0,
        "errors": []
    }
    
    try:
        await status.emit_analysis_started(session_id, project_path)
        await status.emit_step(session_id, "diff_analyzer", "started", "Analyzing commit for security issues...")
        
        diff_analyzer = DiffAnalyzerAgent()
        
        all_vulnerabilities = await diff_analyzer.analyze_commit_with_context(
            diff_content, 
            commit_message, 
            file_contents, 
            changed_lines
        )
        
        report["vulnerabilities"] = [v.to_dict() for v in all_vulnerabilities]
        report["cost"] = diff_analyzer.execution.total_cost if diff_analyzer.execution else 0
        
        await status.emit_step(session_id, "diff_analyzer", "completed", f"Found {len(all_vulnerabilities)} issues", {"count": len(all_vulnerabilities)})
        
        for v in all_vulnerabilities:
            await status.emit_vulnerability_found(session_id, v.to_dict())
        
        report["summary"] = diff_analyzer.get_results()["by_severity"]
        report["summary"]["total_vulnerabilities"] = len(all_vulnerabilities)
        report["status"] = "completed"
        report["completed_at"] = time.time()
        
        await status.emit_analysis_completed(session_id, report["summary"])
        
    except Exception as e:
        logger.error(f"[{session_id}] Diff analysis error: {e}")
        report["status"] = "failed"
        report["errors"].append(str(e))
        report["completed_at"] = time.time()
        await status.emit_analysis_failed(session_id, str(e))
    
    report_path = os.path.join(REPORTS_DIR, f"{session_id}.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    if report["status"] == "completed":
        update_stats_from_report(report)
    
    logger.info(f"[{session_id}] Diff analysis complete")


@app.post("/api/v1/analysis/corpus")
async def analyze_corpus(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Analyze fuzzer corpus inputs to decode their format"""
    config = get_llm_config()
    if not config.has_any_key():
        raise HTTPException(status_code=503, detail="No LLM API keys configured")
    
    inputs = request.get("inputs", [])
    harness_code = request.get("harness_code", "")
    session_id = request.get("session_id", f"corpus_{int(time.time())}")
    
    if not inputs:
        raise HTTPException(status_code=400, detail="At least one input is required")
    
    background_tasks.add_task(run_corpus_analysis, session_id, inputs, harness_code)
    
    return {
        "session_id": session_id,
        "status": "started",
        "analysis_type": "corpus"
    }


async def run_corpus_analysis(session_id: str, inputs: List[str], harness_code: str):
    """Run corpus format analysis"""
    logger.info(f"Starting corpus analysis for session {session_id}")
    status = get_status_service()
    
    report = {
        "session_id": session_id,
        "analysis_type": "corpus",
        "started_at": time.time(),
        "status": "running",
        "input_formats": [],
        "summary": {},
        "cost": 0.0,
        "errors": []
    }
    
    try:
        await status.emit_analysis_started(session_id, "corpus")
        await status.emit_step(session_id, "harness_decoder", "started", "Decoding input formats...")
        
        harness_decoder = HarnessDecoderAgent()
        
        try:
            samples = []
            for inp in inputs[:10]:
                try:
                    samples.append(bytes.fromhex(inp.strip()))
                except ValueError:
                    samples.append(inp.encode())
            
            if len(samples) == 1:
                input_format = await harness_decoder.decode_input(samples[0], harness_code)
            else:
                input_format = await harness_decoder.infer_format(samples)
            
            if input_format:
                report["input_formats"] = [input_format.to_dict()]
            
            report["cost"] = harness_decoder.execution.total_cost if harness_decoder.execution else 0
            
            await status.emit_step(session_id, "harness_decoder", "completed", 
                f"Decoded {len(report['input_formats'])} format(s)", {})
            
        except Exception as decode_error:
            logger.warning(f"[{session_id}] Decode error: {decode_error}")
            report["errors"].append(str(decode_error))
        
        report["summary"] = {
            "inputs_analyzed": len(inputs),
            "formats_decoded": len(report["input_formats"]),
            "fields_found": sum(len(f.get("fields", [])) for f in report["input_formats"])
        }
        report["status"] = "completed"
        report["completed_at"] = time.time()
        
        await status.emit_analysis_completed(session_id, report["summary"])
        
    except Exception as e:
        logger.error(f"[{session_id}] Corpus analysis error: {e}")
        report["status"] = "failed"
        report["errors"].append(str(e))
        report["completed_at"] = time.time()
        await status.emit_analysis_failed(session_id, str(e))
    
    report_path = os.path.join(REPORTS_DIR, f"{session_id}.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"[{session_id}] Corpus analysis complete")


@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    agents = create_agents()
    return {
        "agents": {
            agent_id: {
                "agent_id": agent_id,
                "model": agent.model,
                "status": "available",
                "available_tools": len(agent.get_tools())
            }
            for agent_id, agent in agents.items()
        },
        "total_agents": len(agents),
        "active_sessions": 0
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
