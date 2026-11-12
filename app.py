"""Run: python app.py. Uses only the Python standard library."""
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from engine import simulate

ROOT = Path(__file__).parent
class Handler(BaseHTTPRequestHandler):
    def send(self, status, data, mime):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path == '/logo.svg':
            return self.send(200,(ROOT/'logo.svg').read_bytes(),'image/svg+xml')
        if self.path == '/logo.png':
            return self.send(200,(ROOT/'logo.png').read_bytes(),'image/png')
        if self.path != '/':
            return self.send(404,b'Not found','text/plain')
        self.send(200,(ROOT/'trace.html').read_bytes(),'text/html; charset=utf-8')
    def do_POST(self):
        if self.path != '/api/review':
            return self.send(404,b'Not found','text/plain')
        try:
            length = int(self.headers.get('Content-Length',0))
            if length > 20000:
                raise ValueError('Request too large')
            result = simulate(json.loads(self.rfile.read(length)))
            self.send(200,json.dumps(result).encode(),'application/json')
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            self.send(400,json.dumps({'error':str(error)}).encode(),'application/json')

if __name__ == '__main__':
    try:
        server = ThreadingHTTPServer(('127.0.0.1',8000),Handler)
    except OSError:
        server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    address = f'http://127.0.0.1:{server.server_port}'
    print(f'TRACE is ready: open {address} (keep this window open; Ctrl+C to stop)',flush=True)
    if '--open' in sys.argv:
        threading.Timer(0.7, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
