import os
import socket
import threading
import time
import subprocess
import paramiko
from dotenv import load_dotenv
import sys

load_dotenv()

SERVER_HOST = os.getenv("SERVER_HOST")
SERVER_PORT = int(os.getenv("SERVER_PORT", "22"))
SERVER_USER = os.getenv("SERVER_USER")
SERVER_PASSWORD = os.getenv("SERVER_PASSWORD")
LOCAL_PORT = int(os.getenv("POSTGRES_PORT", "5434"))

def wait_for_port(port, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def start_tunnel():
    print(f"Подключаемся к {SERVER_USER}@{SERVER_HOST}:{SERVER_PORT}...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        SERVER_HOST,
        port=SERVER_PORT,
        username=SERVER_USER,
        password=SERVER_PASSWORD
    )
    
    transport = client.get_transport()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("127.0.0.1", LOCAL_PORT))
    server_sock.listen(5)

    def handle(local_sock):
        try:
            channel = transport.open_channel(
                "direct-tcpip",
                ("127.0.0.1", 5432),
                ("127.0.0.1", LOCAL_PORT)
            )
            def forward(src, dst):
                while True:
                    try:
                        data = src.recv(4096)
                        if not data:
                            break
                        dst.send(data)
                    except:
                        break
            t1 = threading.Thread(target=forward, args=(local_sock, channel), daemon=True)
            t2 = threading.Thread(target=forward, args=(channel, local_sock), daemon=True)
            t1.start()
            t2.start()
        except Exception as e:
            print(f"Ошибка канала: {e}")

    def accept_loop():
        while True:
            try:
                local_sock, _ = server_sock.accept()
                threading.Thread(target=handle, args=(local_sock,), daemon=True).start()
            except:
                break

    threading.Thread(target=accept_loop, daemon=True).start()
    print(f"Туннель активен на порту {LOCAL_PORT}!")
    return client, server_sock

if __name__ == "__main__":
    client, server_sock = start_tunnel()
    
    if not wait_for_port(LOCAL_PORT):
        print("Туннель не поднялся!")
        exit(1)

    try:
        print("Запускаем миграции...")
        command = sys.argv[1] if len(sys.argv) > 1 else "upgrade"

        if command == "revision":
            message = sys.argv[2] if len(sys.argv) > 2 else "migration"
            result = subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", message],
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        else:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        if result.returncode == 0:
            print("Миграции применены успешно!")
        else:
            print("Ошибка при миграции!")
    finally:
        server_sock.close()
        client.close()
        print("Туннель закрыт.")