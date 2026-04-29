import socket
import threading
import time
import webbrowser

import uvicorn
import webview


def find_free_port(start: int = 8000, end: int = 9000) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found")


def run_server(port: int) -> None:
    uvicorn.run("app:app", host="127.0.0.1", port=port, log_level="warning")


def main() -> None:
    port = find_free_port()
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()

    url = f"http://127.0.0.1:{port}"

    for _ in range(40):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    else:
        webbrowser.open(url)
        return

    webview.create_window("Personal Assistant", url=url, width=1200, height=800)
    webview.start()


if __name__ == "__main__":
    main()
