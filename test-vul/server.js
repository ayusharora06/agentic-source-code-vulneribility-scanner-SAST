/*
 * Vulnerable Node.js REST API Server
 * Contains intentional security vulnerabilities for testing
 */

const express = require('express');
const mysql = require('mysql');
const jwt = require('jsonwebtoken');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const app = express();
app.use(express.json());

// VULN: Hardcoded secret key
const JWT_SECRET = 'super_secret_key_123';

// VULN: Hardcoded database credentials
const db = mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: 'password123',  // VULN: Hardcoded password
    database: 'users_db'
});

// VULN: SQL Injection in login
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    
    // VULN: Direct string concatenation - SQL Injection
    const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;
    
    db.query(query, (err, results) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        
        if (results.length > 0) {
            // VULN: Weak JWT with hardcoded secret
            const token = jwt.sign({ user: username, admin: false }, JWT_SECRET);
            res.json({ token, message: 'Login successful' });
        } else {
            res.status(401).json({ error: 'Invalid credentials' });
        }
    });
});

// VULN: NoSQL Injection (if using MongoDB)
app.post('/api/users/search', (req, res) => {
    const { filter } = req.body;
    
    // VULN: Directly using user input as query filter
    // This allows: {"$gt": ""} to match all documents
    User.find(filter, (err, users) => {
        res.json(users);
    });
});

// VULN: Path Traversal
app.get('/api/files/:filename', (req, res) => {
    const filename = req.params.filename;
    
    // VULN: No sanitization - allows ../../../etc/passwd
    const filepath = path.join('/uploads', filename);
    
    fs.readFile(filepath, 'utf8', (err, data) => {
        if (err) {
            return res.status(404).json({ error: 'File not found' });
        }
        res.send(data);
    });
});

// VULN: Command Injection
app.post('/api/ping', (req, res) => {
    const { host } = req.body;
    
    // VULN: User input directly in shell command
    exec(`ping -c 4 ${host}`, (error, stdout, stderr) => {
        if (error) {
            return res.status(500).json({ error: stderr });
        }
        res.json({ output: stdout });
    });
});

// VULN: Insecure Direct Object Reference (IDOR)
app.get('/api/users/:id/profile', (req, res) => {
    const userId = req.params.id;
    
    // VULN: No authorization check - any user can access any profile
    const query = `SELECT * FROM users WHERE id = ${userId}`;
    
    db.query(query, (err, results) => {
        if (results.length > 0) {
            // VULN: Exposing sensitive data including password hash
            res.json(results[0]);
        } else {
            res.status(404).json({ error: 'User not found' });
        }
    });
});

// VULN: Mass Assignment
app.put('/api/users/:id', (req, res) => {
    const userId = req.params.id;
    const updates = req.body;
    
    // VULN: Allows updating any field including is_admin
    // Attacker can send: { "is_admin": true }
    const fields = Object.keys(updates).map(k => `${k} = '${updates[k]}'`).join(', ');
    const query = `UPDATE users SET ${fields} WHERE id = ${userId}`;
    
    db.query(query, (err) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        res.json({ message: 'User updated' });
    });
});

// VULN: Server-Side Request Forgery (SSRF)
app.post('/api/fetch-url', async (req, res) => {
    const { url } = req.body;
    
    // VULN: No URL validation - can access internal services
    // Attacker can send: http://localhost:6379/ (Redis)
    // Or: http://169.254.169.254/latest/meta-data/ (AWS metadata)
    try {
        const response = await fetch(url);
        const data = await response.text();
        res.json({ data });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// VULN: Reflected XSS
app.get('/api/search', (req, res) => {
    const { q } = req.query;
    
    // VULN: Reflecting user input without encoding
    res.send(`<html><body>Search results for: ${q}</body></html>`);
});

// VULN: Insecure Deserialization
app.post('/api/import', (req, res) => {
    const { data } = req.body;
    
    // VULN: Deserializing untrusted data
    try {
        const obj = eval('(' + data + ')');  // VULN: eval with user input
        res.json({ imported: obj });
    } catch (error) {
        res.status(400).json({ error: 'Invalid data' });
    }
});

// VULN: Weak password reset
app.post('/api/reset-password', (req, res) => {
    const { email } = req.body;
    
    // VULN: Predictable reset token
    const resetToken = Date.now().toString();
    
    // VULN: Token stored in URL parameter
    const resetLink = `http://example.com/reset?token=${resetToken}&email=${email}`;
    
    res.json({ message: 'Reset email sent', debug_link: resetLink });  // VULN: Exposing reset link
});

// VULN: Missing rate limiting
app.post('/api/bruteforce-login', (req, res) => {
    // No rate limiting - allows unlimited login attempts
    const { username, password } = req.body;
    
    const query = `SELECT * FROM users WHERE username = ? AND password = ?`;
    db.query(query, [username, password], (err, results) => {
        res.json({ success: results.length > 0 });
    });
});

// VULN: Verbose error messages
app.use((err, req, res, next) => {
    // VULN: Exposing stack traces and internal details
    res.status(500).json({
        error: err.message,
        stack: err.stack,
        query: err.sql  // VULN: Exposing SQL queries
    });
});

app.listen(3000, () => {
    console.log('Vulnerable server running on port 3000');
});
