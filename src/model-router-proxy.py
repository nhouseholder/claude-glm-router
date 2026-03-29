#!/usr/bin/env python3
"""Claude Code Multi-Model Router Proxy v6
Routes Haiku→Z AI (GLM-5.1), Opus/Sonnet→Anthropic.
Strips thinking blocks for seamless model switching.
"""
import http.server
import http.client
import json
import ssl
import sys
import os
import socketserver
import socket
import threading
import time
import logging
from logging.handlers import RotatingFileHandler

PORT = 17532
ZAI_API_KEY = os.environ.get("ZAI_API_KEY", "d8047c5f5b4246fd9a94b672adfe4882.t2Sn4v37ISjM4IaE")
ANTHROPIC_HOST = "api.anthropic.com"
ZAI_HOST = "api.z.ai"
ZAI_PATH = "/api/anthropic/v1/messages"
ANTHROPIC_PATH = "/v1/messages"

# Timeout: 5 minutes covers even long Opus thinking responses
UPSTREAM_TIMEOUT = 300

# Track last routed model for banner queries
_last_route = {"model": "unknown", "backend": "unknown", "timestamp": 0}
_route_lock = threading.Lock()

# --- Logging setup (rotating, max 5MB, keep 2 backups) ---
log_path = os.environ.get("PROXY_LOG_PATH", "/tmp/proxy.log")
logger = logging.getLogger("model-router")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=2)
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(handler)


def strip_thinking_blocks(messages):
    """Remove thinking/redacted_thinking blocks from message history.
    Prevents signature errors when switching between Opus and Haiku/GLM-5.1."""
    cleaned = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            new_content = [
                block for block in content
                if not (isinstance(block, dict) and block.get("type") in ("thinking", "redacted_thinking"))
            ]
            if not new_content:
                continue
            msg = dict(msg)
            msg["content"] = new_content
        cleaned.append(msg)
    return cleaned


def truncate_messages_for_glm(data, target_chars=400000, keep_recent=5):
    """Semantic message compression for GLM-5.1 context window.

    Strategy: Preserve system prompt + last N messages (recent/important).
    Drop from middle first (older context is less relevant). Only drop from
    start (system message) as last resort.

    Returns (data, dropped_count).
    """
    messages = data.get("messages", [])
    dropped = 0

    while len(json.dumps(data)) > target_chars and len(messages) > keep_recent + 1:
        # Keep: system message (index 0) + last keep_recent messages
        # Drop from: middle messages (indices 1 to -keep_recent)
        if len(messages) > keep_recent + 1:
            # Find middle message with smallest content (least important)
            middle_start = 1
            middle_end = len(messages) - keep_recent
            if middle_start < middle_end:
                # Drop the smallest message in the middle
                min_idx = middle_start
                min_size = len(json.dumps(messages[min_idx]))
                for i in range(middle_start + 1, middle_end):
                    size = len(json.dumps(messages[i]))
                    if size < min_size:
                        min_idx = i
                        min_size = size
                messages.pop(min_idx)
                dropped += 1
            else:
                break
        else:
            break

    # Last resort: drop from end of non-recent messages
    while len(json.dumps(data)) > target_chars and len(messages) > 2:
        if len(messages) > keep_recent + 1:
            messages.pop(1)  # Drop from index 1 (oldest non-system)
            dropped += 1
        else:
            break

    data["messages"] = messages
    return data, dropped


def strip_zai_unsupported(data):
    """Remove fields that Z AI / GLM-5.1 doesn't support."""
    data.pop("betas", None)
    data.pop("anthropic_beta", None)
    # GLM-5 doesn't support extended thinking — strip from all locations
    data.pop("thinking", None)  # Top-level thinking config
    if "metadata" in data:
        metadata = data.get("metadata", {})
        if isinstance(metadata, dict):
            metadata.pop("thinking", None)
    # Also strip temperature/top_k if thinking was enabled (Anthropic constraint)
    # Z AI handles these independently so no issue, but clean up just in case
    return data


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # SO_REUSEPORT on macOS to eliminate TOCTOU race on port binding
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass
        super().server_bind()


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Suppress default request logging; we log selectively

    def do_POST(self):
        global _last_route
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            data = json.loads(raw_body) if raw_body else {}
            model = data.get("model", "")
            use_zai = "haiku" in model.lower()
            ctx = ssl.create_default_context()

            # Always strip thinking blocks — enables seamless model switching
            if "messages" in data:
                data["messages"] = strip_thinking_blocks(data["messages"])

            if use_zai:
                data["model"] = "glm-5.1"
                data = strip_zai_unsupported(data)
                data, dropped = truncate_messages_for_glm(data)
                if dropped:
                    logger.info(f"[truncate] dropped {dropped} oldest messages to fit GLM-5.1 context window")
                send_body = json.dumps(data).encode("utf-8")
                headers = {
                    "content-type": "application/json",
                    "content-length": str(len(send_body)),
                    "x-api-key": ZAI_API_KEY,
                    "anthropic-version": self.headers.get("anthropic-version", "2023-06-01"),
                }
                host, path = ZAI_HOST, ZAI_PATH
                backend = "Z AI (GLM-5.1)"
            else:
                send_body = json.dumps(data).encode("utf-8")
                headers = {
                    "content-type": "application/json",
                    "content-length": str(len(send_body)),
                    "anthropic-version": self.headers.get("anthropic-version", "2023-06-01"),
                }
                # Forward ALL auth headers for Anthropic passthrough
                for h in ["x-api-key", "authorization", "anthropic-beta",
                          "anthropic-dangerous-direct-browser-access", "cookie"]:
                    v = self.headers.get(h)
                    if v:
                        headers[h] = v
                host, path = ANTHROPIC_HOST, ANTHROPIC_PATH
                backend = "Anthropic"

            # Track routing for banner queries
            with _route_lock:
                _last_route = {
                    "model": model,
                    "backend": backend,
                    "timestamp": time.time()
                }

            logger.info(f"[route] {model} → {backend}")

            # Connect with generous timeout for long responses
            conn = http.client.HTTPSConnection(host, timeout=UPSTREAM_TIMEOUT, context=ctx)
            try:
                conn.request("POST", path, body=send_body, headers=headers)
                resp = conn.getresponse()

                # Z AI fallback: if Z AI returns 5xx or connection fails, retry via Anthropic
                if use_zai and resp.status >= 500:
                    logger.warning(f"[fallback] Z AI returned {resp.status} — falling back to Anthropic")
                    conn.close()
                    # Rebuild request for Anthropic using original data
                    fallback_data = json.loads(raw_body) if raw_body else {}
                    if "messages" in fallback_data:
                        fallback_data["messages"] = strip_thinking_blocks(fallback_data["messages"])
                    fallback_body = json.dumps(fallback_data).encode("utf-8")
                    fallback_headers = {
                        "content-type": "application/json",
                        "content-length": str(len(fallback_body)),
                        "anthropic-version": self.headers.get("anthropic-version", "2023-06-01"),
                    }
                    for h in ["x-api-key", "authorization", "anthropic-beta",
                              "anthropic-dangerous-direct-browser-access", "cookie"]:
                        v = self.headers.get(h)
                        if v:
                            fallback_headers[h] = v
                    conn = http.client.HTTPSConnection(ANTHROPIC_HOST, timeout=UPSTREAM_TIMEOUT, context=ctx)
                    conn.request("POST", ANTHROPIC_PATH, body=fallback_body, headers=fallback_headers)
                    resp = conn.getresponse()
                    with _route_lock:
                        _last_route = {"model": model, "backend": "Anthropic (fallback)", "timestamp": time.time()}
                    logger.info(f"[fallback] Z AI → Anthropic fallback succeeded, status={resp.status}")

                self.send_response(resp.status)

                # Forward response headers, handling streaming correctly
                is_streaming = False
                for key, val in resp.getheaders():
                    lower_key = key.lower()
                    if lower_key == "transfer-encoding" and val.lower() == "chunked":
                        is_streaming = True
                        continue  # We'll handle chunked encoding ourselves
                    if lower_key in ("connection", "keep-alive"):
                        continue
                    self.send_header(key, val)

                self.end_headers()

                # Stream response back — larger chunks for better throughput
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        # Client disconnected (user cancelled, new request, etc)
                        logger.info("[route] Client disconnected mid-stream")
                        break
            finally:
                conn.close()

        except (ConnectionRefusedError, ConnectionResetError, socket.timeout) as e:
            # Network errors — if Z AI failed, try Anthropic fallback
            if use_zai:
                logger.warning(f"[fallback] Z AI connection failed ({e}) — falling back to Anthropic")
                try:
                    fallback_data = json.loads(raw_body) if raw_body else {}
                    if "messages" in fallback_data:
                        fallback_data["messages"] = strip_thinking_blocks(fallback_data["messages"])
                    fallback_body = json.dumps(fallback_data).encode("utf-8")
                    fallback_headers = {
                        "content-type": "application/json",
                        "content-length": str(len(fallback_body)),
                        "anthropic-version": self.headers.get("anthropic-version", "2023-06-01"),
                    }
                    for h in ["x-api-key", "authorization", "anthropic-beta",
                              "anthropic-dangerous-direct-browser-access", "cookie"]:
                        v = self.headers.get(h)
                        if v:
                            fallback_headers[h] = v
                    ctx = ssl.create_default_context()
                    conn = http.client.HTTPSConnection(ANTHROPIC_HOST, timeout=UPSTREAM_TIMEOUT, context=ctx)
                    conn.request("POST", ANTHROPIC_PATH, body=fallback_body, headers=fallback_headers)
                    resp = conn.getresponse()
                    self.send_response(resp.status)
                    for key, val in resp.getheaders():
                        lk = key.lower()
                        if lk in ("transfer-encoding", "connection", "keep-alive"):
                            continue
                        self.send_header(key, val)
                    self.end_headers()
                    while True:
                        chunk = resp.read(4096)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    conn.close()
                    with _route_lock:
                        _last_route = {"model": model, "backend": "Anthropic (fallback)", "timestamp": time.time()}
                    logger.info(f"[fallback] Z AI → Anthropic connection fallback succeeded")
                    return
                except Exception as fb_err:
                    logger.error(f"[fallback] Anthropic fallback also failed: {fb_err}")
            logger.warning(f"[error] Upstream connection failed: {e}")
            try:
                self.send_error(502, f"Upstream connection failed: {e}")
            except Exception:
                pass
        except Exception as e:
            logger.error(f"[error] {e}")
            try:
                self.send_error(500, str(e))
            except Exception:
                pass

    def do_GET(self):
        if self.path == "/health":
            with _route_lock:
                last = dict(_last_route)
            body = json.dumps({
                "status": "ok",
                "version": 6,
                "port": PORT,
                "routing": {
                    "haiku": "Z AI (GLM-5.1)",
                    "opus": "Anthropic",
                    "sonnet": "Anthropic"
                },
                "thinking_strip": "enabled",
                "last_route": last,
                "uptime_seconds": int(time.time() - _start_time)
            })
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode())
        elif self.path == "/last-route":
            # Lightweight endpoint for banner hook to query actual routing
            with _route_lock:
                last = dict(_last_route)
            body = json.dumps(last)
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode())
        else:
            self.send_error(404)


def port_in_use(port):
    """Check if another process is listening on the port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0


_start_time = time.time()


def run():
    if port_in_use(PORT):
        # Verify the existing process is actually healthy
        try:
            import urllib.request
            resp = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3)
            data = json.loads(resp.read())
            if data.get("status") == "ok":
                logger.info(f"[model-router] Healthy proxy already running on port {PORT} — exiting.")
                sys.exit(0)
        except Exception:
            # Port is held by a dead/stuck process — try to take over
            logger.warning(f"[model-router] Port {PORT} held by unhealthy process — attempting takeover.")

    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), ProxyHandler)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            logger.info(f"[model-router] Port {PORT} in use (bind failed) — exiting cleanly.")
            sys.exit(0)
        raise

    logger.info(f"[model-router] Proxy v6 started on http://127.0.0.1:{PORT}")
    sys.stderr.write(f"[model-router] Proxy v6 started on http://127.0.0.1:{PORT}\n")
    sys.stderr.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    run()
