#!/usr/bin/env python3
"""
Test script for the Vulnerability Analysis System
Demonstrates basic functionality of agents and API
"""

import asyncio
import sys
import os
import tempfile

# Add the backend src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend/src'))

from agents import create_agent_manager_with_defaults
from agents.vuln_analyzer import Vulnerability


async def test_agents():
    """Test the agent system"""
    print("🤖 Testing Agent System...")
    
    # Create agent manager
    manager = create_agent_manager_with_defaults()
    
    # Start a test session
    session_id = "test_session_001"
    agents = manager.start_session(session_id, ['vuln_analyzer', 'patch_producer', 'triage_agent'])
    
    print(f"✅ Created session {session_id} with {len(agents)} agents")
    
    # Test vulnerability analyzer
    vuln_analyzer = agents['vuln_analyzer']
    
    # Create a test C file with vulnerabilities
    test_code = '''
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
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write(test_code)
        test_file = f.name
    
    try:
        print(f"🔍 Analyzing test file: {test_file}")
        
        # Analyze the test file
        result = await vuln_analyzer.process_message(
            "analyze file",
            {"file_path": test_file}
        )
        
        print(f"📊 Analysis result: {result}")
        
        # Get discovered vulnerabilities
        vulns = vuln_analyzer.get_discovered_vulnerabilities()
        print(f"🚨 Found {len(vulns)} vulnerabilities:")
        
        for vuln in vulns:
            print(f"  - {vuln.vuln_type} ({vuln.severity}): {vuln.description}")
        
        # Test triage agent
        if vulns:
            triage_agent = agents['triage_agent']
            print(f"📋 Triaging vulnerabilities...")
            
            for vuln in vulns:
                await triage_agent.process_message(
                    "triage vulnerability",
                    {"vulnerability": vuln.to_dict()}
                )
            
            triage_results = triage_agent.get_triage_results()
            print(f"📈 Triage completed for {len(triage_results)} vulnerabilities:")
            
            for triage in triage_results:
                print(f"  - {triage.vulnerability_id}: {triage.priority.value} priority, risk score {triage.risk_score}")
        
        # Test patch producer
        if vulns:
            patch_producer = agents['patch_producer']
            print(f"🔧 Generating patches...")
            
            for vuln in vulns:
                await patch_producer.process_message(
                    "generate patch",
                    {"vulnerability": vuln.to_dict()}
                )
            
            patches = patch_producer.get_generated_patches()
            print(f"✨ Generated {len(patches)} patches:")
            
            for patch in patches:
                print(f"  - {patch.patch_id}: {patch.patch_description} (confidence: {patch.confidence:.2f})")
        
        # Complete all executions
        for agent in agents.values():
            agent.complete_execution()
        
        # Get session summary
        summary = manager.get_session_summary(session_id)
        print(f"\n📊 Session Summary:")
        print(f"  Total cost: ${summary.get('total_cost', 0):.4f}")
        print(f"  Total messages: {summary.get('total_messages', 0)}")
        print(f"  Total tool calls: {summary.get('total_tool_calls', 0)}")
        
        return True
        
    finally:
        # Clean up test file
        os.unlink(test_file)


async def test_pattern_analysis():
    """Test pattern analysis functionality"""
    print("\n🔍 Testing Pattern Analysis...")
    
    # Import the agent directly
    from agents.vuln_analyzer import VulnAnalyzerAgent
    
    agent = VulnAnalyzerAgent()
    
    # Test various vulnerability patterns
    test_cases = [
        ("Buffer overflow", "char buf[64]; strcpy(buf, user_input);", "c"),
        ("SQL injection", "query = \"SELECT * FROM users WHERE id = \" + user_id", "python"),
        ("XSS", "element.innerHTML = user_input;", "javascript"),
        ("Format string", "printf(user_input);", "c"),
    ]
    
    for test_name, code, language in test_cases:
        print(f"  Testing {test_name} detection...")
        vulns = await agent._pattern_analysis(code, language)
        
        if vulns:
            print(f"    ✅ Detected: {vulns[0].vuln_type}")
        else:
            print(f"    ❌ Not detected")


def test_database_schema():
    """Test database schema creation"""
    print("\n💾 Testing Database Schema...")
    
    try:
        import asyncio
        from database.models import Database, VulnerabilityRecord
        import time
        
        async def test_db():
            # Create test database
            db = Database("test_vulnerability.db")
            await db.initialize()
            
            print("✅ Database initialized successfully")
            
            # Test inserting a vulnerability record
            vuln_record = VulnerabilityRecord(
                vuln_id="test_vuln_001",
                session_id="test_session",
                vuln_type="Buffer Overflow",
                severity="high",
                description="Test vulnerability",
                file_path="/test/file.c",
                line_number=42,
                tool_source="test",
                confidence=0.9,
                created_at=time.time(),
                metadata="{}"
            )
            
            await db.insert_vulnerability(vuln_record)
            print("✅ Vulnerability record inserted")
            
            # Test retrieving records
            vulns = await db.get_vulnerabilities_by_session("test_session")
            print(f"✅ Retrieved {len(vulns)} vulnerability records")
            
            await db.close()
            
            # Clean up test database
            import os
            os.unlink("test_vulnerability.db")
            
            return True
        
        return asyncio.run(test_db())
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting Vulnerability Analysis System Tests\n")
    
    tests = [
        ("Agent System", test_agents()),
        ("Pattern Analysis", test_pattern_analysis()),
        ("Database Schema", test_database_schema()),
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    print(f"\n📊 Test Results:")
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)