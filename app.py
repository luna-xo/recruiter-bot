import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import db

ROUTES = [
    ("GET", r"^/candidates$", lambda conn, m: db.list_candidates(conn)),
    ("GET", r"^/jobs$", lambda conn, m: db.list_jobs(conn)),
    ("GET", r"^/jobs/(\d+)/matches$", lambda conn, m: db.matches_for_job(conn, int(m.group(1)))),
    ("GET", r"^/candidates/(\d+)/matches$", lambda conn, m: db.matches_for_candidate(conn, int(m.group(1)))),
]


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body) -> None:
        data = json.dumps(body, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle(self, method: str) -> None:
        path = self.path.split("?")[0].rstrip("/") or "/"
        if method == "GET" and path in ("/", "/index.html"):
            data = (db.BASE / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        conn = db.connect()
        try:
            if method == "POST" and path == "/seed":
                db.seed(conn)
                self._send(200, {"status": "seeded"})
                return
            for route_method, pattern, fn in ROUTES:
                m = re.match(pattern, path)
                if route_method == method and m:
                    result = fn(conn, m)
                    if result is None:
                        self._send(404, {"error": "not found"})
                    else:
                        self._send(200, result)
                    return
            self._send(404, {"error": "not found"})
        finally:
            conn.close()

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


def main(port: int = 8000) -> None:
    conn = db.connect()
    db.init_db(conn)
    if db.is_empty(conn):
        db.seed(conn)
    conn.close()
    print(f"Recruiter Bot running on http://localhost:{port}")
    ThreadingHTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
