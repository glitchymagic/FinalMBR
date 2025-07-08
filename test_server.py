#!/usr/bin/env python3
import http.server
import socketserver
import webbrowser
import threading
import time

PORT = 8888

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'''
        <html>
        <head><title>Test Server</title></head>
        <body>
        <h1>Test Server Working!</h1>
        <p>If you can see this, the server is running correctly.</p>
        <p>You can now try the dashboard at: <a href="http://localhost:3000">http://localhost:3000</a></p>
        </body>
        </html>
        ''')

with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
    print(f"Test server running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()