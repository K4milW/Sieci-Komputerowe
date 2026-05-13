#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define DEFAULT_PORT 80
#define BUFFER_SIZE 1024

const char* http_header = "HTTP/1.0 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n";

int main(int argc, char *argv[]) {

    if (getuid() == 0) {
        fprintf(stderr, "Błąd: Uruchamianie serwera z konta root jest zabronione!\n");
        exit(EXIT_FAILURE);
    }

    int port = DEFAULT_PORT;
    if (argc > 1) {
        port = atoi(argv[1]);
    }

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) {
        perror("Błąd: socket");
        exit(EXIT_FAILURE);
    }

    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == -1) {
        perror("Błąd: setsockopt");
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in addr;
    memset((char*)&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY); 
    addr.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        perror("Błąd: bind");
        exit(EXIT_FAILURE);
    }

    if (listen(server_fd, 5) == -1) {
        perror("Błąd: listen");
        exit(EXIT_FAILURE);
    }

    printf("Serwer uruchomiony na porcie %d...\n", port);
    while (1) {
        int client_fd = accept(server_fd, NULL, NULL);
        if (client_fd == -1) {
            perror("Błąd: accept");
            continue; 
        }

        char buffer[BUFFER_SIZE];
        ssize_t bytes_received = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        if (bytes_received == -1) {
            perror("Błąd: recv");
        } else {
            FILE *uptime_file = fopen("/proc/uptime", "r");
            double uptime_val = 0.0;
            if (uptime_file != NULL) {
                fscanf(uptime_file, "%lf", &uptime_val);
                fclose(uptime_file);
            }

            char body[128];
            snprintf(body, sizeof(body), "%.2f", uptime_val);
            int content_length = strlen(body);

            char full_header[512];
            snprintf(full_header, sizeof(full_header), "%sContent-Length: %d\r\n\r\n", http_header, content_length);<s
            if (send(client_fd, full_header, strlen(full_header), 0) == -1) {
                perror("Błąd: send (header)");
            }
            if (send(client_fd, body, strlen(body), 0) == -1) {
                perror("Błąd: send (body)");
            }
        }
        if (shutdown(client_fd, SHUT_WR) == -1) {
            perror("Błąd: shutdown");
        }
        if (close(client_fd) == -1) {
            perror("Błąd: close (klient)");
        }
    }
    close(server_fd);
    return 0;
}