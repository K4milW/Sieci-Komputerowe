import socket
import select
import sys

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

def run_client(nickname):
    server_addr = (SERVER_HOST, SERVER_PORT)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setblocking(False)
    client_socket.sendto(b"\0" + nickname.encode('utf-8'), server_addr)
    
    print(f"Połączono jako '{nickname}'. Możesz zacząć pisać (wpisz 'exit', aby wyjść).")

    try:
        while True:
            ready_to_read, _, _ = select.select([sys.stdin, client_socket], [], [])
            
            for source in ready_to_read:
                if source == sys.stdin:
                    msg = sys.stdin.readline()
                    
                    if not msg or msg.strip() == 'exit':
                        client_socket.sendto(b"", server_addr)
                        return
                    
                    client_socket.sendto(b"\1" + msg.encode('utf-8'), server_addr)
                
                elif source == client_socket:
                    try:
                        data, _ = client_socket.recvfrom(4096)
                        print(data.decode('utf-8'), end="")
                    except BlockingIOError:
                        pass
                    
    except KeyboardInterrupt:
        client_socket.sendto(b"", server_addr)
    finally:
        client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python client.py <TwojNickname>")
        sys.exit(1)
        
    run_client(sys.argv[1])