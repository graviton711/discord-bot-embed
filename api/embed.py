from http.server import BaseHTTPRequestHandler
import json
import os
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
EMBED_SECRET = os.environ.get("EMBED_SECRET", "")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "models/gemini-embedding-001")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Auth check
        auth = self.headers.get("Authorization", "")
        if not EMBED_SECRET or auth != f"Bearer {EMBED_SECRET}":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized"}')
            return

        # Parse body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
            text = data.get("text", "")
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        if not text:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Missing text"}')
            return

        # Call Gemini
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text
            )
            embedding = result.embeddings[0].values
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"embedding": embedding}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
