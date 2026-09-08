import asyncio
import logging
import os

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("storepulse.simulator")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
STORE_CODE = os.getenv("STORE_CODE", "MAD-MADRID")
HEARTBEAT_INTERVAL = float(os.getenv("HEARTBEAT_INTERVAL", "5"))

if HEARTBEAT_INTERVAL <= 0:
    raise ValueError("HEARTBEAT_INTERVAL must be positive")


async def run() -> None:
    endpoint = f"{BACKEND_URL}/api/v1/stores/{STORE_CODE}/heartbeat"
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            try:
                response = await client.post(endpoint)
                response.raise_for_status()
                logger.info("heartbeat accepted store=%s", STORE_CODE)
            except httpx.HTTPError as exc:
                logger.warning("heartbeat failed store=%s error=%s", STORE_CODE, exc)
            await asyncio.sleep(HEARTBEAT_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run())
