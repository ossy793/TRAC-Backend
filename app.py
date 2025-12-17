from flask import Flask, jsonify
from flask_cors import CORS
from models import db
from config import Config
from routes import auth_bp, prediction_bp, verification_bp
from services.data_analysis import data_analysis_service
import os


def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize CORS - IMPORTANT FOR PRODUCTION
    CORS(app,
         resources={
             r"/api/*": {
                 "origins": Config.CORS_ORIGINS,
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization"],
                 "supports_credentials": True
             }
         },
         origins=Config.CORS_ORIGINS,  # Also set at app level
         supports_credentials=True)

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(prediction_bp, url_prefix='/api/predict')
    app.register_blueprint(verification_bp, url_prefix='/api/verify')

    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database initialized")
        except Exception as e:
            print(f"⚠️  Database initialization warning: {e}")

        # Load traffic data
        try:
            data_file = os.path.join('data', 'traffic_data.csv')
            if os.path.exists(data_file):
                result = data_analysis_service.load_traffic_data(data_file)
                if result.get('success'):
                    print(f"✅ Traffic data loaded: {result.get('rows')} rows")
            else:
                print(f"⚠️  Traffic data file not found, creating sample data...")
                data_analysis_service.load_traffic_data()
                print("✅ Sample traffic data created")
        except Exception as e:
            print(f"⚠️  Could not load traffic data: {e}")

    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'success': True,
            'message': 'Smart Traffic Management System API',
            'version': '2.0.0',
            'blockchain': 'Polygon (Mumbai Testnet)',
            'status': 'online',
            'endpoints': {
                'auth': {
                    'register': 'POST /api/auth/register',
                    'login': 'POST /api/auth/login',
                    'drivers': 'GET /api/auth/drivers'
                },
                'prediction': {
                    'route': 'POST /api/predict/route',
                    'hotspots': 'GET /api/predict/accident-hotspots',
                    'statistics': 'GET /api/predict/statistics'
                },
                'verification': {
                    'verify': 'POST /api/verify/driver',
                    'by_wallet': 'GET /api/verify/wallet/<address>',
                    'validity': 'GET /api/verify/check-validity/<license>',
                    'blockchain_status': 'GET /api/verify/blockchain-status'
                }
            }
        })

    # Health check endpoint - IMPORTANT: Add CORS headers
    @app.route('/health')
    def health():
        response = jsonify({
            'success': True,
            'status': 'healthy',
            'services': {
                'database': 'connected',
                'api': 'running',
                'blockchain': 'polygon-mumbai'
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

    return app


# For Render deployment
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=Config.DEBUG
    )