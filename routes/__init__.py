import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from .auth import auth_bp
from .prediction import prediction_bp
from .verification import verification_bp

__all__ = ['auth_bp', 'prediction_bp', 'verification_bp']