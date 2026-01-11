import sys
from interface.gui.main_window import main as gui_main
from utils.logger import logger
from interface.gui.styles import AppTheme
from PyQt6.QtWidgets import QApplication

def main():
    logger.info("Starting GVPA...")
    try:
        # We need to access the QApplication instance to apply the theme
        # gui_main() usually creates it. Let's see if we can hook in or if gui_main 
        # needs to be refactored. 
        # Actually, gui_main in main_window.py creates QApplication.
        # Let's import AppTheme inside main_window.py instead or modify main_window.py
        # But wait, main.py calls gui_main(). 
        # Let's check main_window.py's main function.
        gui_main()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("GVPA exited normally.")

if __name__ == "__main__":
    main()
