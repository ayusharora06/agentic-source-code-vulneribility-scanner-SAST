/*
 * Vulnerable Go WebSocket Server
 * Contains intentional security vulnerabilities for testing
 */

package main

import (
	"crypto/md5"
	"crypto/tls"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"sync"

	"github.com/gorilla/websocket"
	_ "github.com/lib/pq"
)

// VULN: Hardcoded credentials
const (
	DB_HOST     = "localhost"
	DB_USER     = "postgres"
	DB_PASSWORD = "admin123" // VULN: Hardcoded password
	DB_NAME     = "users"
	SECRET_KEY  = "my_secret_key_123" // VULN: Hardcoded secret
)

var (
	db       *sql.DB
	upgrader = websocket.Upgrader{
		// VULN: Allowing all origins - no CORS protection
		CheckOrigin: func(r *http.Request) bool {
			return true
		},
	}
)

type User struct {
	ID       int    `json:"id"`
	Username string `json:"username"`
	Password string `json:"password"`
	Email    string `json:"email"`
	IsAdmin  bool   `json:"is_admin"`
}

type Message struct {
	Type    string      `json:"type"`
	Payload interface{} `json:"payload"`
}

// VULN: Race Condition - shared counter without proper synchronization
var requestCounter int
var balance = 1000

func incrementCounter() {
	// VULN: Race condition - not thread-safe
	temp := requestCounter
	temp++
	requestCounter = temp
}

// VULN: Race condition in balance update
func withdraw(amount int) bool {
	// VULN: TOCTOU race condition
	if balance >= amount {
		// Time gap allows double spending
		balance -= amount
		return true
	}
	return false
}

// VULN: SQL Injection
func loginHandler(w http.ResponseWriter, r *http.Request) {
	username := r.FormValue("username")
	password := r.FormValue("password")

	// VULN: SQL Injection through string concatenation
	query := fmt.Sprintf("SELECT * FROM users WHERE username = '%s' AND password = '%s'", username, password)

	rows, err := db.Query(query)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	if rows.Next() {
		var user User
		rows.Scan(&user.ID, &user.Username, &user.Password, &user.Email, &user.IsAdmin)
		// VULN: Returning password in response
		json.NewEncoder(w).Encode(user)
	} else {
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
	}
}

// VULN: Command Injection
func pingHandler(w http.ResponseWriter, r *http.Request) {
	host := r.URL.Query().Get("host")

	// VULN: User input directly in command execution
	cmd := exec.Command("sh", "-c", "ping -c 4 "+host)
	output, err := cmd.Output()

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Write(output)
}

// VULN: Path Traversal
func fileHandler(w http.ResponseWriter, r *http.Request) {
	filename := r.URL.Query().Get("file")

	// VULN: No path sanitization - allows ../../../etc/passwd
	filepath := "/var/data/" + filename

	data, err := ioutil.ReadFile(filepath)
	if err != nil {
		http.Error(w, "File not found", http.StatusNotFound)
		return
	}

	w.Write(data)
}

// VULN: Insecure TLS Configuration
func createInsecureClient() *http.Client {
	// VULN: Skipping TLS certificate verification
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}
	return &http.Client{Transport: tr}
}

// VULN: SSRF
func fetchHandler(w http.ResponseWriter, r *http.Request) {
	url := r.URL.Query().Get("url")

	// VULN: No URL validation - can access internal services
	client := createInsecureClient()
	resp, err := client.Get(url)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	body, _ := ioutil.ReadAll(resp.Body)
	w.Write(body)
}

// VULN: Weak Password Hashing
func hashPassword(password string) string {
	// VULN: MD5 is cryptographically broken
	hash := md5.Sum([]byte(password))
	return hex.EncodeToString(hash[:])
}

// VULN: Unvalidated Redirect
func redirectHandler(w http.ResponseWriter, r *http.Request) {
	target := r.URL.Query().Get("url")

	// VULN: Open redirect - no validation
	http.Redirect(w, r, target, http.StatusFound)
}

// VULN: Information Disclosure
func debugHandler(w http.ResponseWriter, r *http.Request) {
	// VULN: Exposing sensitive system information
	info := map[string]interface{}{
		"hostname":  os.Getenv("HOSTNAME"),
		"db_host":   DB_HOST,
		"db_user":   DB_USER,
		"secret":    SECRET_KEY,
		"env_vars":  os.Environ(), // VULN: Exposing all env vars
		"go_version": "go version",
	}

	json.NewEncoder(w).Encode(info)
}

// WebSocket handler with vulnerabilities
func wsHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("Upgrade error:", err)
		return
	}
	defer conn.Close()

	for {
		var msg Message
		err := conn.ReadJSON(&msg)
		if err != nil {
			break
		}

		switch msg.Type {
		case "command":
			// VULN: Command injection via WebSocket
			cmd := msg.Payload.(string)
			output, _ := exec.Command("sh", "-c", cmd).Output()
			conn.WriteJSON(Message{Type: "result", Payload: string(output)})

		case "query":
			// VULN: SQL Injection via WebSocket
			query := msg.Payload.(string)
			rows, _ := db.Query(query)
			defer rows.Close()
			conn.WriteJSON(Message{Type: "result", Payload: "Query executed"})

		case "file":
			// VULN: Path traversal via WebSocket
			filename := msg.Payload.(string)
			data, _ := ioutil.ReadFile("/data/" + filename)
			conn.WriteJSON(Message{Type: "result", Payload: string(data)})
		}
	}
}

// VULN: Buffer issue - potential panic
func processBuffer(data []byte) {
	// VULN: No bounds checking
	result := make([]byte, 10)
	copy(result, data[:20]) // Panic if data < 20 bytes
	fmt.Println(string(result))
}

// VULN: Goroutine leak
func leakyHandler(w http.ResponseWriter, r *http.Request) {
	ch := make(chan string)

	go func() {
		// VULN: Goroutine may never complete if channel not read
		result := "processed"
		ch <- result
	}()

	// VULN: Not always reading from channel
	select {
	case <-r.Context().Done():
		return
	default:
		w.Write([]byte("OK"))
		// ch never read - goroutine leaks
	}
}

// VULN: Mutex deadlock potential
var mu1, mu2 sync.Mutex

func deadlockFunc1() {
	mu1.Lock()
	defer mu1.Unlock()
	mu2.Lock() // VULN: Can deadlock if deadlockFunc2 called concurrently
	defer mu2.Unlock()
}

func deadlockFunc2() {
	mu2.Lock()
	defer mu2.Unlock()
	mu1.Lock() // VULN: Deadlock - opposite lock order
	defer mu1.Unlock()
}

func main() {
	var err error
	connStr := fmt.Sprintf("host=%s user=%s password=%s dbname=%s sslmode=disable",
		DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)

	db, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	http.HandleFunc("/login", loginHandler)
	http.HandleFunc("/ping", pingHandler)
	http.HandleFunc("/file", fileHandler)
	http.HandleFunc("/fetch", fetchHandler)
	http.HandleFunc("/redirect", redirectHandler)
	http.HandleFunc("/debug", debugHandler)
	http.HandleFunc("/ws", wsHandler)
	http.HandleFunc("/leaky", leakyHandler)

	// VULN: Running on all interfaces without TLS
	log.Println("Starting vulnerable server on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
