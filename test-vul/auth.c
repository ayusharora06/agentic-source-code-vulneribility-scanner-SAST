/*
 * Vulnerable Authentication System
 * Contains intentional security vulnerabilities for testing
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAX_USERS 100
#define ADMIN_PASSWORD "admin123"  // VULN: Hardcoded credentials

typedef struct {
    char username[32];
    char password[32];
    int is_admin;
} User;

User users[MAX_USERS];
int user_count = 0;

// VULN: Buffer overflow - no bounds checking
void login(char *username, char *password) {
    char buffer[64];
    char query[256];
    
    // VULN: strcpy without length check - buffer overflow
    strcpy(buffer, username);
    strcat(buffer, ":");
    strcat(buffer, password);
    
    // VULN: Format string vulnerability
    printf("Attempting login: ");
    printf(username);  // User input directly in format string
    printf("\n");
    
    // VULN: sprintf without bounds - buffer overflow
    sprintf(query, "SELECT * FROM users WHERE username='%s' AND password='%s'", username, password);
    
    // Check hardcoded admin
    if (strcmp(username, "admin") == 0 && strcmp(password, ADMIN_PASSWORD) == 0) {
        printf("Admin login successful!\n");
        return;
    }
    
    for (int i = 0; i < user_count; i++) {
        if (strcmp(users[i].username, username) == 0 && 
            strcmp(users[i].password, password) == 0) {
            printf("Login successful for user: %s\n", username);
            return;
        }
    }
    
    printf("Login failed!\n");
}

// VULN: No input validation, buffer overflow possible
void register_user(char *username, char *password) {
    if (user_count >= MAX_USERS) {
        printf("Max users reached\n");
        return;
    }
    
    // VULN: strcpy without bounds checking
    strcpy(users[user_count].username, username);
    strcpy(users[user_count].password, password);  // VULN: Storing plaintext password
    users[user_count].is_admin = 0;
    user_count++;
    
    printf("User registered: %s\n", username);
}

// VULN: Command injection
void check_user_files(char *username) {
    char command[256];
    
    // VULN: User input directly in system command
    sprintf(command, "ls -la /home/%s", username);
    system(command);  // Command injection vulnerability
}

// VULN: Integer overflow
void allocate_session(int size) {
    // VULN: No check for negative or overflow
    char *session = (char *)malloc(size * sizeof(char));
    if (session == NULL) {
        printf("Allocation failed\n");
        return;
    }
    
    memset(session, 0, size);
    printf("Session allocated: %d bytes\n", size);
    // VULN: Memory leak - session never freed
}

// VULN: Use after free
void process_token(char *token) {
    char *token_copy = strdup(token);
    
    if (strlen(token_copy) > 10) {
        free(token_copy);
    }
    
    // VULN: Use after free - token_copy may have been freed
    printf("Processing token: %s\n", token_copy);
}

// VULN: Race condition in file access
int check_and_read_config(char *filepath) {
    FILE *fp;
    char buffer[1024];
    
    // VULN: TOCTOU race condition
    if (access(filepath, R_OK) == 0) {
        // Time gap between check and use
        fp = fopen(filepath, "r");
        if (fp) {
            fread(buffer, 1, 1024, fp);
            fclose(fp);
            return 1;
        }
    }
    return 0;
}

int main(int argc, char *argv[]) {
    char username[256];
    char password[256];
    
    printf("=== Vulnerable Auth System ===\n");
    printf("1. Login\n");
    printf("2. Register\n");
    printf("3. Check Files\n");
    printf("Choice: ");
    
    int choice;
    scanf("%d", &choice);
    
    // VULN: gets() is dangerous - removed from C11
    printf("Username: ");
    scanf("%s", username);  // VULN: No length limit
    
    printf("Password: ");
    scanf("%s", password);  // VULN: Password visible, no length limit
    
    switch(choice) {
        case 1:
            login(username, password);
            break;
        case 2:
            register_user(username, password);
            break;
        case 3:
            check_user_files(username);
            break;
        default:
            printf("Invalid choice\n");
    }
    
    return 0;
}
