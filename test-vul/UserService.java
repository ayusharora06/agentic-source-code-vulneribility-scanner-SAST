/*
 * Vulnerable Java User Service
 * Contains intentional security vulnerabilities for testing
 */

package com.vulnerable.service;

import java.io.*;
import java.sql.*;
import java.util.*;
import java.security.MessageDigest;
import javax.servlet.http.*;
import javax.xml.parsers.*;
import org.xml.sax.InputSource;

public class UserService {
    
    // VULN: Hardcoded credentials
    private static final String DB_URL = "jdbc:mysql://localhost:3306/users";
    private static final String DB_USER = "root";
    private static final String DB_PASSWORD = "admin123";  // VULN: Hardcoded password
    
    private Connection connection;
    
    public UserService() throws SQLException {
        connection = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
    }
    
    // VULN: SQL Injection
    public User login(String username, String password) throws SQLException {
        // VULN: String concatenation in SQL query
        String query = "SELECT * FROM users WHERE username = '" + username + 
                       "' AND password = '" + password + "'";
        
        Statement stmt = connection.createStatement();
        ResultSet rs = stmt.executeQuery(query);  // SQL Injection vulnerability
        
        if (rs.next()) {
            User user = new User();
            user.setId(rs.getInt("id"));
            user.setUsername(rs.getString("username"));
            user.setPassword(rs.getString("password"));  // VULN: Returning password
            user.setEmail(rs.getString("email"));
            return user;
        }
        return null;
    }
    
    // VULN: Path Traversal
    public String readUserFile(String filename) throws IOException {
        // VULN: No path validation - allows ../../../etc/passwd
        String basePath = "/var/data/users/";
        File file = new File(basePath + filename);
        
        BufferedReader reader = new BufferedReader(new FileReader(file));
        StringBuilder content = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            content.append(line).append("\n");
        }
        reader.close();
        return content.toString();
    }
    
    // VULN: Command Injection
    public String backupUserData(String userId) throws IOException {
        // VULN: User input in runtime command
        String command = "tar -czf /backups/user_" + userId + ".tar.gz /data/users/" + userId;
        
        Runtime runtime = Runtime.getRuntime();
        Process process = runtime.exec(command);  // Command injection vulnerability
        
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        return reader.readLine();
    }
    
    // VULN: Insecure Deserialization
    public Object loadUserSession(byte[] data) throws Exception {
        // VULN: Deserializing untrusted data
        ByteArrayInputStream bis = new ByteArrayInputStream(data);
        ObjectInputStream ois = new ObjectInputStream(bis);
        return ois.readObject();  // Insecure deserialization
    }
    
    // VULN: XXE (XML External Entity)
    public User parseUserXml(String xmlData) throws Exception {
        // VULN: XXE vulnerability - external entities enabled by default
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        // Missing: factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        
        DocumentBuilder builder = factory.newDocumentBuilder();
        InputSource is = new InputSource(new StringReader(xmlData));
        org.w3c.dom.Document doc = builder.parse(is);
        
        User user = new User();
        user.setUsername(doc.getElementsByTagName("username").item(0).getTextContent());
        return user;
    }
    
    // VULN: Weak Cryptography
    public String hashPassword(String password) throws Exception {
        // VULN: Using MD5 which is cryptographically broken
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] hash = md.digest(password.getBytes());
        
        // VULN: No salt used
        StringBuilder sb = new StringBuilder();
        for (byte b : hash) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
    
    // VULN: LDAP Injection
    public boolean authenticateLdap(String username, String password) {
        // VULN: LDAP injection through string concatenation
        String filter = "(&(uid=" + username + ")(userPassword=" + password + "))";
        
        // Simulated LDAP query
        System.out.println("LDAP Filter: " + filter);
        return true;
    }
    
    // VULN: Open Redirect
    public void handleRedirect(HttpServletResponse response, String targetUrl) throws IOException {
        // VULN: No validation of redirect URL
        response.sendRedirect(targetUrl);  // Open redirect vulnerability
    }
    
    // VULN: Sensitive Data Exposure in Logs
    public void createUser(String username, String password, String creditCard) {
        // VULN: Logging sensitive information
        System.out.println("Creating user: " + username + " with password: " + password);
        System.out.println("Credit card: " + creditCard);
        
        // Simulated user creation
    }
    
    // VULN: Race Condition
    private int accountBalance = 1000;
    
    public void withdraw(int amount) {
        // VULN: Race condition - check and modify not atomic
        if (accountBalance >= amount) {
            // Time gap allows double withdrawal
            try { Thread.sleep(100); } catch (Exception e) {}
            accountBalance -= amount;
            System.out.println("Withdrawn: " + amount + ", Balance: " + accountBalance);
        }
    }
    
    // VULN: Null Pointer Dereference
    public String getUserEmail(String username) throws SQLException {
        String query = "SELECT email FROM users WHERE username = ?";
        PreparedStatement stmt = connection.prepareStatement(query);
        stmt.setString(1, username);
        ResultSet rs = stmt.executeQuery();
        
        // VULN: Not checking if result exists before accessing
        rs.next();
        return rs.getString("email").toLowerCase();  // NPE if no result
    }
    
    // VULN: Resource Leak
    public List<User> getAllUsers() throws SQLException {
        List<User> users = new ArrayList<>();
        Statement stmt = connection.createStatement();
        ResultSet rs = stmt.executeQuery("SELECT * FROM users");
        
        while (rs.next()) {
            User user = new User();
            user.setId(rs.getInt("id"));
            user.setUsername(rs.getString("username"));
            users.add(user);
        }
        // VULN: Statement and ResultSet never closed - resource leak
        return users;
    }
    
    // VULN: Trust Boundary Violation
    public void processRequest(HttpServletRequest request) {
        String userInput = request.getParameter("data");
        
        // VULN: Storing untrusted data in session without validation
        request.getSession().setAttribute("trusted_data", userInput);
    }
    
    // Inner class for User
    public static class User implements Serializable {
        private int id;
        private String username;
        private String password;
        private String email;
        
        // Getters and setters
        public int getId() { return id; }
        public void setId(int id) { this.id = id; }
        public String getUsername() { return username; }
        public void setUsername(String username) { this.username = username; }
        public String getPassword() { return password; }
        public void setPassword(String password) { this.password = password; }
        public String getEmail() { return email; }
        public void setEmail(String email) { this.email = email; }
    }
}
