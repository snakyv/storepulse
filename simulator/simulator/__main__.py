import asyncio
import logging
import os

from simulator.config import SimulatorConfig
from simulator.runtime import run

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


if __name__ == "__main__":
    asyncio.run(run(SimulatorConfig.from_env(os.environ)))
