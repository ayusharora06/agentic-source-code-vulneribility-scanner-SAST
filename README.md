# 🛡️ Agentic Ethical Hacker

Advanced vulnerability analysis tool powered by AI agents.

## 🎯 Overview

A multi-agent LLM-powered security analysis system with a modern, real-time web interface for practical vulnerability analysis and ethical hacking workflows. It provides automated vulnerability detection, intelligent triage, and AI-generated patches through a user-friendly dashboard.

## ✨ Key Features

### 🤖 AI-Powered Multi-Agent System
- **Vulnerability Analyzer**: Automated code vulnerability discovery using static analysis
- **Patch Producer**: AI-generated security patches with confidence scoring
- **Triage Agent**: Intelligent vulnerability prioritization and risk assessment
- **Real-time Coordination**: Agents work together seamlessly with live updates

### 🔍 Advanced Security Analysis
- **Pattern Detection**: Built-in vulnerability patterns for C/C++, Python, JavaScript
- **Static Analysis**: Integration with Infer and Clang Static Analyzer
- **Multi-Language Support**: C/C++, Python, JavaScript, TypeScript, Java
- **Confidence Scoring**: Each finding includes confidence levels and explanations

### 📊 Modern Dashboard
- **Real-Time Updates**: WebSocket-powered live vulnerability feed
- **Vulnerability Timeline**: Chronological discovery tracking with filtering
- **Agent Status**: Live monitoring of agent activities and tool usage
- **Interactive Interface**: Click-to-analyze with drag-and-drop file support

## 🚀 Quick Start

### Option 1: One-Command Start (Recommended)
```bash
# Clone and start everything
git clone <repository>
cd agentic-Ethical-hacker-roboduck
./scripts/quick_start.sh
```

### Option 2: Manual Setup

#### Prerequisites
- **Python 3.8+** - [Download from python.org](https://python.org)
- **Node.js 18+** - [Download from nodejs.org](https://nodejs.org)
- **Git** - For cloning the repository

#### Backend Setup
```bash
# Start backend server
./scripts/start_backend.sh

# Or manually:
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
# Start frontend server (in new terminal)
./scripts/start_frontend.sh

# Or manually:
cd frontend
npm install
npm run dev
```

#### Access the Application
- **Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🏗️ System Architecture

```
agentic-ethical-hacker-roboduck/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── agents/         # AI agents (vuln_analyzer, patch_producer, triage_agent)
│   │   ├── api/           # REST API endpoints and WebSocket manager
│   │   ├── database/      # SQLite database models and schemas
│   │   └── config/        # Application configuration
│   └── requirements.txt   # Python dependencies
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/          # Next.js app router pages
│   │   ├── components/   # React components
│   │   └── hooks/        # Custom React hooks
│   └── package.json      # Node.js dependencies
├── scripts/              # Startup and utility scripts
└── docs/                 # Documentation
```

## 💡 How It Works

1. **Upload or Analyze**: Upload source files, analyze projects, or paste code snippets
2. **Agent Processing**: Multiple AI agents analyze the code simultaneously:
   - Pattern matching for known vulnerabilities
   - Static analysis using industry tools
   - AI-powered code review and assessment
3. **Real-Time Results**: Watch vulnerabilities appear in real-time as they're discovered
4. **Intelligent Triage**: Automatic prioritization based on severity, exploitability, and business impact
5. **Patch Generation**: AI creates security patches with explanations and test suggestions

## 🔧 Agent Capabilities

### Vulnerability Analyzer
- **Pattern Analysis**: Detects buffer overflows, injection flaws, XSS, format strings
- **Tool Integration**: Infer and Clang Static Analyzer support
- **Multi-Language**: C/C++, Python, JavaScript, TypeScript, Java
- **Confidence Scoring**: Each finding rated for accuracy

### Patch Producer  
- **Automated Fixes**: Generates secure code replacements
- **Multiple Strategies**: Direct fixes, mitigations, and workarounds
- **Test Suggestions**: Recommends test cases for patches
- **Validation**: Checks patches for syntax and logic errors

### Triage Agent
- **Risk Scoring**: CVSS-style scoring with business context
- **Priority Assignment**: Critical, High, Medium, Low classifications
- **Timeline Recommendations**: Immediate, 1-week, 1-month, next-release
- **Impact Assessment**: Technical and business impact analysis

## 🛠️ Configuration

### Environment Variables (Backend)
```bash
# Optional: AI API Keys for enhanced analysis
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database
DATABASE_URL=vulnerability_analysis.db

# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### Tool Integration
The system automatically detects and integrates with:
- **Infer** (Facebook's static analyzer) - `brew install infer` or download from infer.liginc.com
- **Clang** (LLVM static analyzer) - Usually pre-installed on macOS/Linux

## 📊 Example Analysis

```bash
# Test the system with a vulnerable C file
echo '
#include <stdio.h>
#include <string.h>

int main() {
    char buffer[64];
    char input[256];
    
    // Vulnerable: buffer overflow
    strcpy(buffer, input);
    
    // Vulnerable: format string  
    printf(input);
    
    return 0;
}' > test_vuln.c

# Upload via dashboard or use API
curl -X POST http://localhost:8000/analysis/start \
  -H "Content-Type: application/json" \
  -d '{"type": "file", "target": "test_vuln.c"}'
```

**Expected Results**:
- 2 vulnerabilities detected (Buffer Overflow, Format String)
- Both triaged as "High" priority
- AI-generated patches replacing `strcpy` with `strncpy` and fixing `printf`
- Real-time updates showing discovery and analysis progress

## 🧪 Testing

```bash
# Run system tests
python3 scripts/test_system.py

# Test individual components
cd backend
python3 -c "from src.agents import VulnAnalyzerAgent; print('✅ Agents working')"

cd frontend  
npm run lint
npm run type-check
```

## 🔒 Security & Limitations

### Security Features
- Input validation and sanitization
- Safe code execution in isolated environments
- No external network access during analysis
- Secure WebSocket connections

### Current Limitations
- **Local Analysis Only**: No network scanning capabilities (unlike full pentest tools)
- **Static Analysis Focus**: Limited dynamic analysis compared to specialized tools
- **AI Dependencies**: Enhanced features require API keys for AI models
- **Beta Software**: This is a demonstration/educational tool

### Extending Capabilities
To add network security testing, integrate with:
- **Nmap** for port scanning
- **Burp Suite** for web application testing
- **Metasploit** for exploitation frameworks
- **OWASP ZAP** for web security scanning

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Open Source Community**: For the security tools and frameworks that make this possible

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: See the `/docs` folder for detailed guides
- **Examples**: Check `/examples` for sample analyses and integrations

---

**⚠️ Disclaimer**: This tool is for educational and authorized security testing only. Always obtain proper authorization before analyzing code or systems you don't own.