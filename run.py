#!/usr/bin/env python3
import os
import sys
import asyncio
from aiohttp import web
from bot.main import main as bot_main
from telegram.ext import Application

async def webhook_handler(request):
    """Обрабатывает вебхук от Telegram."""
    if request.match_info.get('token') != os.getenv('BOT_TOKEN').split(':')[1]:
        return web.Response(status=403)
    
    update = await request.json()
    application = request.app['application']
    await application.update_queue.put(update)
    return web.Response()

async def start_bot(app):
    """Запускает бота."""
    app['application'] = await bot_main(return_app=True)

async def cleanup_bot(app):
    """Останавливает бота."""
    if 'application' in app:
        await app['application'].stop()
        await app['application'].shutdown()

async def main():
    """Запускает веб-сервер."""
    app = web.Application()
    app.on_startup.append(start_bot)
    app.on_cleanup.append(cleanup_bot)
    app.router.add_post(f"/webhook/{{token}}", webhook_handler)
    
    port = int(os.getenv('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"🌍 Вебхук запущен на порту {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
