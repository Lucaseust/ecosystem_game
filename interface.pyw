"""Double-cliquez pour ouvrir la commande de séance ECOSYSTEM."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from launcher import main

if __name__ == "__main__":
    main()
