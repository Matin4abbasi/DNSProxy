
import socket

HOST = "127.0.0.1"
PORT = 5354

request_count = 0

def start_server():
    global request_count

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))

    print(f"Upstream server listening on {HOST}:{PORT}")

    try:
        while True:
            data, client_address = server.recvfrom(1024)

            request_count += 1

            message = data.decode("utf-8").strip()
            parts = message.split()

            if len(parts) == 2 and parts[0] == "QUERY":
                domain = parts[1]

                if domain == "missing.example.net":
                    response = "NOT_FOUND"
                else:
                    response = "OK 198.51.100.7 5"
            else:
                domain = "INVALID_REQUEST"
                response = "SERVER_ERROR"

            server.sendto(
                response.encode("utf-8"),
                client_address
            )

            print(
                f"Request #{request_count}: "
                f"{domain} -> {response}"
            )

    except KeyboardInterrupt:
        print("\nUpstream server stopped.")

    finally:
        server.close()


if __name__ == "__main__":
    start_server()
