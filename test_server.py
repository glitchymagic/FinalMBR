#!/usr/bin/env python3
from flask import Flask
import socket

app = Flask(__name__)

@app.route('/')
def home():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connection Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .success {{ color: green; }}
            .info {{ color: blue; }}
        </style>
    </head>
    <body>
        <h1>Connection Test Successful!</h1>
        <p class="success">✅ If you can see this page, your connection to the test server is working.</p>
        <p class="info">Hostname: {hostname}</p>
        <p class="info">Local IP: {local_ip}</p>
        <p>Try accessing the main dashboard at:</p>
        <ul>
            <li><a href="http://127.0.0.1:3000">http://127.0.0.1:3000</a></li>
            <li><a href="http://localhost:3000">http://localhost:3000</a></li>
        </ul>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    print("Starting test server on port 8080...")
    print("Access at http://127.0.0.1:8080 or http://localhost:8080")
    app.run(host='0.0.0.0', port=8080)