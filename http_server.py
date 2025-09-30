import asyncio
import logging
import sys
from aiohttp import web
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

class HeartbeatServer:
    def __init__(self):
        self.last_request_time = datetime.now()
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        self.app.router.add_get('/heartbeat', self.handle_heartbeat)
        self.app.router.add_head('/heartbeat', self.handle_heartbeat)
        self.app.router.add_get('/', self.handle_root)
        
    async def handle_heartbeat(self, request):
        self.last_request_time = datetime.now()
        response_data = {
            "status": "alive",
            "timestamp": self.last_request_time.isoformat(),
            "message": "Bot is running and receiving requests"
        }
        return web.json_response(response_data, status=200)
    
    async def handle_root(self, request):
        return web.json_response({
            "status": "service running",
            "endpoint": "/heartbeat for health check"
        }, status=200)

    def start_server(self, port=10000):
        logger.info(f"🚀 Starting heartbeat server on port {port}")
        web.run_app(self.app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    server = HeartbeatServer()
    server.start_server()
