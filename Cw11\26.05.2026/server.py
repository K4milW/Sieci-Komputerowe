import socket

# Konfiguracja serwera
HOST = '127.0.0.1'
PORT = 12345

def run_server():
    # Inicjalizacja socketu datagramowego (UDP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    
    print(f"Serwer nasłuchuje na {HOST}:{PORT}...")
    clients = {}

    try:
        while True:
            data, addr = server_socket.recvfrom(4096)
            
            if data == b"":
                if addr in clients:
                    print(f"Użytkownik {clients[addr].decode('utf-8')} ({addr}) rozłączył się.")
                    del clients[addr]
                continue
 
            prefix = data[:1]
            
            if prefix == b"\0":
                nickname = data[1:]
                clients[addr] = nickname
                print(f"Zarejestrowano: {nickname.decode('utf-8')} z adresu {addr}")
                
            elif prefix == b"\1":
                if addr in clients:
                    sender_nick = clients[addr]
                    message = data[1:]
                    broadcast_msg = sender_nick + b": " + message
                    
                    for client_addr in clients.keys():
                        server_socket.sendto(broadcast_msg, client_addr)
                else:
                    pass
    except KeyboardInterrupt:
        print("\nZamykanie serwera...")
    finally:
        # Teoretyczne zamknięcie serwera
        server_socket.close()

if __name__ == "__main__":
    run_server()