#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Function to display help information
void show_help(const char *program_name) {
    printf("Usage: %s [OPTIONS] [MESSAGE]\n", program_name);
    printf("\nA simple CLI tool that prints messages.\n");
    printf("\nOPTIONS:\n");
    printf("  -h, --help     Show this help message and exit\n");
    printf("  -v, --version  Show version information\n");
    printf("  -u, --upper    Convert message to uppercase\n");
    printf("  -c, --count    Show character count of message\n");
    printf("\nEXAMPLES:\n");
    printf("  %s \"Hello World\"          # Print message\n", program_name);
    printf("  %s -u \"hello world\"       # Print in uppercase\n", program_name);
    printf("  %s -c \"hello\"             # Count characters\n", program_name);
    printf("  %s -h                     # Show this help\n", program_name);
}

// Function to display version information
void show_version() {
    printf("Hello CLI Tool v1.0.0\n");
    printf("Written in C for learning purposes\n");
}

// Function to convert string to uppercase
void to_uppercase(char *str) {
    for (int i = 0; str[i]; i++) {
        if (str[i] >= 'a' && str[i] <= 'z') {
            str[i] = str[i] - 'a' + 'A';
        }
    }
}

int main(int argc, char *argv[]) {
    // Flag variables
    int show_help_flag = 0;
    int show_version_flag = 0;
    int uppercase_flag = 0;
    int count_flag = 0;
    char *message = NULL;
    
    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        // Check for help flags
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            show_help_flag = 1;
        }
        // Check for version flags
        else if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--version") == 0) {
            show_version_flag = 1;
        }
        // Check for uppercase flags
        else if (strcmp(argv[i], "-u") == 0 || strcmp(argv[i], "--upper") == 0) {
            uppercase_flag = 1;
        }
        // Check for count flags
        else if (strcmp(argv[i], "-c") == 0 || strcmp(argv[i], "--count") == 0) {
            count_flag = 1;
        }
        // Check if it starts with - but isn't a known flag
        else if (argv[i][0] == '-') {
            printf("Error: Unknown flag '%s'\n", argv[i]);
            printf("Use -h or --help for usage information.\n");
            return 1;  // Exit with error code
        }
        // Not a flag, treat as message
        else {
            message = argv[i];
        }
    }
    
    // Handle flags in order of priority
    if (show_help_flag) {
        show_help(argv[0]);
        return 0;
    }
    
    if (show_version_flag) {
        show_version();
        return 0;
    }
    
    // If no message provided and we're not just showing help/version
    if (message == NULL) {
        printf("Hello, World!\n");
        printf("This is a simple CLI tool written in C.\n");
        printf("Use -h for help or provide a message to customize output.\n");
        return 0;
    }
    
    // Process the message based on flags
    if (uppercase_flag) {
        // Make a copy to avoid modifying original
        char *upper_message = malloc(strlen(message) + 1);
        strcpy(upper_message, message);
        to_uppercase(upper_message);
        
        printf("Uppercase message: %s\n", upper_message);
        free(upper_message);
    } else {
        printf("Message: %s\n", message);
    }
    
    if (count_flag) {
        printf("Character count: %zu\n", strlen(message));
    }
    
    return 0;  // Success
}
