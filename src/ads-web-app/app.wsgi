import sys, os

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, BASE_DIR)

from app import *

application = create_app()
