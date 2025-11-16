from loguru import logger
from .gui.main_window import run_gui

def main() -> None:
    logger.info("Starting MUTS (starter)")
    run_gui()
