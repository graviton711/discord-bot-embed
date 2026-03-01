from http.server import BaseHTTPRequestHandler
import json
import os
import random
from google import genai

GEMINI_KEYS = [k.strip() for k in os.environ.get("GEMINI_API_KEY", "").split(",") if k.strip()]
EMBED_SECRET = os.environ.get("EMBED_SECRET", "")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "models/gemini-embedding-001")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        auth = self.headers.get("Authorization", "")
        if not EMBED_SECRET or auth != f"Bearer {EMBED_SECRET}":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized"}')
            return

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

        if not text or not GEMINI_KEYS:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Missing text or API keys"}')
            return

        # Key rotation - try up to 3 random keys
        keys_to_try = random.sample(GEMINI_KEYS, min(3, len(GEMINI_KEYS)))
        last_error = None
        for api_key in keys_to_try:
            try:
                client = genai.Client(api_key=api_key)
                result = client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
                embedding = result.embeddings[0].values
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"embedding": embedding}).encode())
                return
            except Exception as e:
                last_error = str(e)
                continue

        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": last_error}).encode())

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
