"""Serve the local portfolio and forward chat to the existing guarded demo."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent

class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if self.path != "/chat":
            return self.send_error(404)
        if self.headers.get("Origin") != f"http://127.0.0.1:{self.server.server_port}":
            return self.send_error(403)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.send_error(400)
        if not 0 < length <= 96000:
            return self.send_error(413)
        request = Request(f"http://127.0.0.1:{self.server.chat_port}/chat", self.rfile.read(length),
                          {"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=180) as response:
                code, body = response.status, response.read()
        except HTTPError as error:
            code, body = error.code, error.read()
        except OSError:
            code, body = 502, b'{"error":"Offline ang lokal na modelo. Subukan ulit mamaya."}'
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=7866)
    parser.add_argument("--chat-port", type=int, default=7864)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), PreviewHandler) as server:
        server.chat_port = args.chat_port
        server.serve_forever()

