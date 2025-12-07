"""
Vulnerable Python Flask API
Contains intentional security vulnerabilities for testing
"""

import os
import pickle
import subprocess
import sqlite3
import hashlib
import yaml
import requests
from flask import Flask, request, jsonify, render_template_string, redirect, session
from functools import wraps

app = Flask(__name__)

# VULN: Hardcoded secret key
app.secret_key = 'super_secret_key_123'

# VULN: Hardcoded database credentials
DB_HOST = 'localhost'
DB_USER = 'admin'
DB_PASSWORD = 'password123'  # VULN: Hardcoded password


def get_db():
    return sqlite3.connect('users.db')


# VULN: SQL Injection
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # VULN: SQL Injection - string formatting in query
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    
    user = cursor.fetchone()
    if user:
        session['user_id'] = user[0]
        return jsonify({'message': 'Login successful', 'user': user})
    
    return jsonify({'error': 'Invalid credentials'}), 401


# VULN: Command Injection
@app.route('/api/ping', methods=['POST'])
def ping_host():
    data = request.json
    host = data.get('host')
    
    # VULN: User input directly in shell command
    result = os.popen(f'ping -c 4 {host}').read()
    
    return jsonify({'output': result})


# VULN: Command Injection via subprocess
@app.route('/api/backup', methods=['POST'])
def backup_data():
    data = request.json
    filename = data.get('filename')
    
    # VULN: shell=True with user input
    cmd = f'tar -czf /backups/{filename}.tar.gz /data/'
    subprocess.call(cmd, shell=True)  # Command injection
    
    return jsonify({'message': f'Backup created: {filename}'})


# VULN: Server-Side Request Forgery (SSRF)
@app.route('/api/fetch', methods=['POST'])
def fetch_url():
    data = request.json
    url = data.get('url')
    
    # VULN: No URL validation - can access internal services
    # Attacker can access: http://localhost:6379, http://169.254.169.254/
    try:
        response = requests.get(url, timeout=10)
        return jsonify({'content': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# VULN: Insecure Deserialization (Pickle)
@app.route('/api/load-session', methods=['POST'])
def load_session():
    data = request.get_data()
    
    # VULN: Deserializing untrusted pickle data
    try:
        obj = pickle.loads(data)  # Remote code execution possible
        return jsonify({'loaded': str(obj)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# VULN: YAML Deserialization
@app.route('/api/parse-config', methods=['POST'])
def parse_config():
    yaml_data = request.get_data().decode('utf-8')
    
    # VULN: yaml.load without safe_load allows code execution
    config = yaml.load(yaml_data)  # Should use yaml.safe_load
    
    return jsonify({'config': config})


# VULN: Path Traversal
@app.route('/api/files/<path:filename>')
def get_file(filename):
    # VULN: No path sanitization - allows ../../../etc/passwd
    base_path = '/var/data/uploads/'
    file_path = base_path + filename
    
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return jsonify({'error': str(e)}), 404


# VULN: Server-Side Template Injection (SSTI)
@app.route('/api/render', methods=['POST'])
def render_template():
    data = request.json
    template = data.get('template')
    
    # VULN: User input in template - allows {{config}} or {{''.__class__.__mro__}}
    return render_template_string(template)


# VULN: Weak Password Hashing
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # VULN: MD5 is cryptographically broken, no salt
    password_hash = hashlib.md5(password.encode()).hexdigest()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password_hash)
    )
    conn.commit()
    
    return jsonify({'message': 'User registered'})


# VULN: Open Redirect
@app.route('/api/redirect')
def handle_redirect():
    target = request.args.get('url')
    
    # VULN: No validation of redirect URL
    return redirect(target)


# VULN: Mass Assignment
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    # VULN: Allows updating any field including is_admin
    for key, value in data.items():
        query = f"UPDATE users SET {key} = '{value}' WHERE id = {user_id}"
        cursor.execute(query)  # Also SQL injection
    
    conn.commit()
    return jsonify({'message': 'User updated'})


# VULN: Sensitive Data Exposure
@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    user = cursor.fetchone()
    
    if user:
        # VULN: Returning sensitive data including password hash
        return jsonify({
            'id': user[0],
            'username': user[1],
            'password_hash': user[2],  # Should not expose
            'email': user[3],
            'ssn': user[4],  # Should not expose
            'credit_card': user[5]  # Should not expose
        })
    
    return jsonify({'error': 'User not found'}), 404


# VULN: Hardcoded API Key
API_KEY = 'sk-1234567890abcdef'  # VULN: Hardcoded secret

@app.route('/api/external-service')
def call_external():
    # VULN: API key in URL
    response = requests.get(f'https://api.example.com/data?key={API_KEY}')
    return jsonify({'data': response.json()})


# VULN: Debug Mode Information Disclosure
@app.route('/api/debug')
def debug_info():
    # VULN: Exposing internal system information
    return jsonify({
        'python_version': os.popen('python --version').read(),
        'env_vars': dict(os.environ),  # VULN: Exposing all env vars
        'cwd': os.getcwd(),
        'user': os.popen('whoami').read()
    })


# VULN: eval() with user input
@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    expression = data.get('expression')
    
    # VULN: eval with user input - Remote Code Execution
    try:
        result = eval(expression)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# VULN: exec() with user input
@app.route('/api/run-code', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code')
    
    # VULN: exec with user input - Remote Code Execution
    try:
        exec(code)
        return jsonify({'message': 'Code executed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# VULN: No CSRF protection, no rate limiting
@app.route('/api/transfer', methods=['POST'])
def transfer_money():
    data = request.json
    to_account = data.get('to')
    amount = data.get('amount')
    
    # VULN: No CSRF token validation
    # VULN: No rate limiting
    return jsonify({
        'message': f'Transferred ${amount} to {to_account}'
    })


if __name__ == '__main__':
    # VULN: Debug mode enabled in production
    app.run(debug=True, host='0.0.0.0', port=5000)
