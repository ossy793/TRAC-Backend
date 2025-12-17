import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///traffic_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Polygon Blockchain Configuration
    POLYGON_RPC_URL = os.environ.get('POLYGON_RPC_URL') or 'https://rpc-mumbai.maticvigil.com'
    CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS') or '0x0000000000000000000000000000000000000000'
    PRIVATE_KEY = os.environ.get('PRIVATE_KEY') or ''

    # Network
    NETWORK = os.environ.get('NETWORK') or 'polygon-mumbai'
    CHAIN_ID = int(os.environ.get('CHAIN_ID') or 80001)

    # API Configuration - IMPORTANT FOR PRODUCTION
    API_HOST = '0.0.0.0'
    API_PORT = int(os.environ.get('PORT', 5000))  # Render uses PORT env variable
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # CORS - IMPORTANT: Add your Vercel domain
    CORS_ORIGINS = [
        "http://localhost:*",
        "http://127.0.0.1:*",
        "https://tracbyteamios.vercel.app",  # Your actual Vercel URL
        "https://*.vercel.app"  # Allow all Vercel preview deployments
    ]

    # AI Model Configuration
    MODEL_PATH = 'models/traffic_predictor.pkl'
    CONFIDENCE_THRESHOLD = 0.75