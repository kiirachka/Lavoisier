from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

logger = logging.getLogger(__name__)

class SimpleHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/heartbeat' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            logger.info("Получен ping от мониторинга")
        else:
            self.send_response(404)
            self.end_headers()

def run_http_server(port=8080):
    """Запускает простой HTTP-сервер для health checks"""
    server = HTTPServer(('0.0.0.0', port), SimpleHealthHandler)
    logger.info(f"HTTP сервер запущен на порту {port}")
    server.serve_forever()

def start_http_server():
    """Запускает HTTP сервер в отдельном потоке"""
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    return http_thread
