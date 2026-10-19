import sys
from pathlib import Path

# ai/ is a folder of packages (generation, evaluation, ...) rather than an installed
# distribution, so tests put it on the path the same way the backend does.
AI_DIR = Path(__file__).resolve().parents[1]
if str(AI_DIR) not in sys.path:
    sys.path.insert(0, str(AI_DIR))
