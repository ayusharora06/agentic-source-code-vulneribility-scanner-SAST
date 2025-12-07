"""
Code Parser - Extract functions and structures using regex patterns
Lightweight parser without tree-sitter dependency for simplicity
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SourceMember:
    name: str
    member_type: str
    file_path: str
    start_line: int
    end_line: int
    signature: str
    body: str
    language: str
    docstring: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "member_type": self.member_type,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "signature": self.signature,
            "body": self.body[:2000] if len(self.body) > 2000 else self.body,
            "language": self.language,
            "docstring": self.docstring
        }


LANGUAGE_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.hpp': 'cpp',
    '.java': 'java',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
}


class CodeParser:
    
    def __init__(self):
        self.patterns = self._build_patterns()
    
    def _build_patterns(self) -> Dict[str, List[Tuple[str, str, re.Pattern]]]:
        return {
            'python': [
                ('function', 'def', re.compile(
                    r'^(\s*)(async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?:',
                    re.MULTILINE
                )),
                ('class', 'class', re.compile(
                    r'^(\s*)class\s+(\w+)\s*(?:\([^)]*\))?\s*:',
                    re.MULTILINE
                )),
            ],
            'javascript': [
                ('function', 'function', re.compile(
                    r'^(\s*)(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{',
                    re.MULTILINE
                )),
                ('function', 'arrow', re.compile(
                    r'^(\s*)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{',
                    re.MULTILINE
                )),
                ('class', 'class', re.compile(
                    r'^(\s*)class\s+(\w+)\s*(?:extends\s+\w+)?\s*\{',
                    re.MULTILINE
                )),
            ],
            'typescript': [
                ('function', 'function', re.compile(
                    r'^(\s*)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
                    re.MULTILINE
                )),
                ('class', 'class', re.compile(
                    r'^(\s*)(?:export\s+)?class\s+(\w+)\s*(?:<[^>]*>)?(?:\s+extends\s+\w+)?\s*\{',
                    re.MULTILINE
                )),
            ],
            'c': [
                ('function', 'function', re.compile(
                    r'^(\s*)(?:static\s+)?(?:inline\s+)?(?:\w+\s*\*?\s+)+(\w+)\s*\([^)]*\)\s*\{',
                    re.MULTILINE
                )),
                ('struct', 'struct', re.compile(
                    r'^(\s*)(?:typedef\s+)?struct\s+(\w+)\s*\{',
                    re.MULTILINE
                )),
            ],
            'cpp': [
                ('function', 'function', re.compile(
                    r'^(\s*)(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:\w+\s*[*&]?\s+)+(\w+)\s*\([^)]*\)\s*(?:const)?\s*(?:override)?\s*\{',
                    re.MULTILINE
                )),
                ('class', 'class', re.compile(
                    r'^(\s*)class\s+(\w+)\s*(?::\s*(?:public|private|protected)\s+\w+)?\s*\{',
                    re.MULTILINE
                )),
            ],
            'java': [
                ('function', 'method', re.compile(
                    r'^(\s*)(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:\w+(?:<[^>]+>)?\s+)+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{',
                    re.MULTILINE
                )),
                ('class', 'class', re.compile(
                    r'^(\s*)(?:public\s+)?(?:abstract\s+)?(?:final\s+)?class\s+(\w+)\s*(?:<[^>]+>)?(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{',
                    re.MULTILINE
                )),
            ],
            'go': [
                ('function', 'func', re.compile(
                    r'^(\s*)func\s+(?:\([^)]+\)\s+)?(\w+)\s*\([^)]*\)\s*(?:\([^)]*\)|\w+)?\s*\{',
                    re.MULTILINE
                )),
                ('struct', 'struct', re.compile(
                    r'^(\s*)type\s+(\w+)\s+struct\s*\{',
                    re.MULTILINE
                )),
            ],
        }
    
    def detect_language(self, file_path: Optional[str] = None, code: Optional[str] = None) -> str:
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in LANGUAGE_EXTENSIONS:
                return LANGUAGE_EXTENSIONS[ext]
        
        if code:
            if 'def ' in code and ':' in code:
                return 'python'
            elif '#include' in code:
                return 'c'
            elif 'func ' in code and 'package ' in code:
                return 'go'
            elif 'public class' in code or 'private class' in code:
                return 'java'
            elif 'function ' in code or '=>' in code:
                return 'javascript'
        
        return 'unknown'
    
    def parse(self, code: str, file_path: Optional[str] = None) -> List[SourceMember]:
        language = self.detect_language(file_path, code)
        
        if language not in self.patterns:
            return self._parse_generic(code, file_path or '<source>', language)
        
        members = []
        lines = code.split('\n')
        
        for member_type, subtype, pattern in self.patterns[language]:
            for match in pattern.finditer(code):
                indent = match.group(1)
                name = match.group(2) if member_type == 'class' else match.group(match.lastindex)
                
                if not name or name in ['if', 'for', 'while', 'switch', 'return']:
                    continue
                
                start_pos = match.start()
                start_line = code[:start_pos].count('\n') + 1
                
                body_start = match.end()
                end_pos = self._find_block_end(code, body_start - 1, language)
                end_line = code[:end_pos].count('\n') + 1
                
                body = code[match.start():end_pos]
                signature = match.group(0).strip()
                
                docstring = self._extract_docstring(code, start_pos, language)
                
                members.append(SourceMember(
                    name=name,
                    member_type=member_type,
                    file_path=file_path or '<source>',
                    start_line=start_line,
                    end_line=end_line,
                    signature=signature,
                    body=body,
                    language=language,
                    docstring=docstring
                ))
        
        return members
    
    def _find_block_end(self, code: str, start: int, language: str) -> int:
        if language == 'python':
            return self._find_python_block_end(code, start)
        else:
            return self._find_brace_block_end(code, start)
    
    def _find_brace_block_end(self, code: str, start: int) -> int:
        brace_pos = code.find('{', start)
        if brace_pos == -1:
            return len(code)
        
        count = 1
        pos = brace_pos + 1
        in_string = False
        string_char = None
        
        while pos < len(code) and count > 0:
            char = code[pos]
            
            if in_string:
                if char == string_char and code[pos-1] != '\\':
                    in_string = False
            else:
                if char in '"\'':
                    in_string = True
                    string_char = char
                elif char == '{':
                    count += 1
                elif char == '}':
                    count -= 1
            
            pos += 1
        
        return pos
    
    def _find_python_block_end(self, code: str, start: int) -> int:
        lines = code[start:].split('\n')
        if not lines:
            return len(code)
        
        first_line = lines[0]
        base_indent = len(first_line) - len(first_line.lstrip())
        
        end_offset = len(first_line) + 1
        
        for line in lines[1:]:
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                end_offset += len(line) + 1
                continue
            
            current_indent = len(line) - len(stripped)
            if current_indent <= base_indent and stripped:
                break
            
            end_offset += len(line) + 1
        
        return start + end_offset
    
    def _extract_docstring(self, code: str, pos: int, language: str) -> Optional[str]:
        if language == 'python':
            after = code[pos:pos+500]
            match = re.search(r':\s*\n\s*("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', after)
            if match:
                return match.group(1).strip('"\' \n')
        
        before = code[max(0, pos-500):pos]
        match = re.search(r'/\*\*([\s\S]*?)\*/\s*$', before)
        if match:
            return match.group(1).strip()
        
        return None
    
    def _parse_generic(self, code: str, file_path: str, language: str) -> List[SourceMember]:
        return [SourceMember(
            name='<module>',
            member_type='module',
            file_path=file_path,
            start_line=1,
            end_line=code.count('\n') + 1,
            signature='',
            body=code,
            language=language
        )]
    
    def get_context(self, code: str, line_number: int, context_lines: int = 5) -> str:
        lines = code.split('\n')
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        return '\n'.join(lines[start:end])


_parser: Optional[CodeParser] = None


def get_parser() -> CodeParser:
    global _parser
    if _parser is None:
        _parser = CodeParser()
    return _parser


def parse_code(code: str, file_path: Optional[str] = None) -> List[SourceMember]:
    return get_parser().parse(code, file_path)


def parse_file(file_path: str) -> List[SourceMember]:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()
    return get_parser().parse(code, file_path)
