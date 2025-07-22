import asyncio
import socket
import os
import logging
import time
from typing import Set, Tuple

# Configure logging for Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 5005))
BUFFER_SIZE = 960  # 480 samples * 2 bytes (int16)
TIMEOUT = 30  # Seconds to consider a client inactive

clients: Set[Tuple[str, int]] = set()
last_active: dict[Tuple[str, int], float] = {}

async def handle_messages():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('0.0.0.0', PORT))
        sock.setblocking(False)
        logger.info(f"UDP Voice Relay Server started on port {PORT}")

        async def cleanup_inactive_clients():
            while True:
                current_time = time.time()
                inactive_clients = {addr for addr, last_time in last_active.items() if current_time - last_time > TIMEOUT}
                for addr in inactive_clients:
                    clients.discard(addr)
                    last_active.pop(addr, None)
                    logger.info(f"Removed inactive client: {addr}")
                await asyncio.sleep(10)

        asyncio.create_task(cleanup_inactive_clients())

        while True:
            try:
                data, addr = await asyncio.get_event_loop().sock_recvfrom(sock, BUFFER_SIZE)
                if len(data) != BUFFER_SIZE:
                    logger.warning(f"Invalid packet size from {addr}: {len(data)} bytes, expected {BUFFER_SIZE}")
                    continue
                clients.add(addr)
                last_active[addr] = time.time()
                logger.debug(f"Received {len(data)} bytes from {addr}, relaying to {len(clients)-1} clients")
                for client in clients:
                    if client != addr:
                        try:
                            await asyncio.get_event_loop().sock_sendto(sock, data, client)
                        except Exception as e:
                            logger.error(f"Failed to send to {client}: {e}")
            except Exception as e:
                logger.error(f"Error in handle_messages: {e}")
                await asyncio.sleep(1)
    finally:
        sock.close()
        logger.info("Socket closed")

async def main():
    try:
        await handle_messages()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
