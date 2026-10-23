import sys
from pathlib import Path

# Project root directory ko sys.path mein add karta hai
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))