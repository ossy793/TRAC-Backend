import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Blueprint, request, jsonify
from models import db, Driver
from services.polygon_service import polygon_service
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new driver"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = [
            'first_name', 'last_name', 'email', 'phone',
            'license_number', 'license_expiry', 'vehicle_plate',
            'insurance_provider', 'insurance_expiry',
            'road_cert_number', 'cert_expiry', 'wallet_address'
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Check if driver already exists
        existing = Driver.query.filter_by(license_number=data['license_number']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Driver with this license number already registered'
            }), 409

        # Register on Polygon blockchain
        blockchain_result = polygon_service.register_driver(data)

        if not blockchain_result.get('success'):
            return jsonify({
                'success': False,
                'error': blockchain_result.get('error', 'Blockchain registration failed')
            }), 500

        tx_hash = blockchain_result.get('transaction_hash')

        # Create new driver in database
        driver = Driver(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data['phone'],
            license_number=data['license_number'],
            license_expiry=datetime.fromisoformat(data['license_expiry']),
            vehicle_plate=data['vehicle_plate'],
            insurance_provider=data['insurance_provider'],
            insurance_expiry=datetime.fromisoformat(data['insurance_expiry']),
            road_cert_number=data['road_cert_number'],
            cert_expiry=datetime.fromisoformat(data['cert_expiry']),
            wallet_address=data['wallet_address'],
            blockchain_tx=tx_hash
        )

        db.session.add(driver)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Driver registered successfully on Polygon blockchain',
            'driver': driver.to_dict(),
            'blockchain_tx': tx_hash,
            'explorer_url': blockchain_result.get('explorer_url')
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a driver"""
    try:
        data = request.get_json()
        email = data.get('email')
        license_number = data.get('license_number')

        driver = Driver.query.filter_by(
            email=email,
            license_number=license_number
        ).first()

        if not driver:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'driver': driver.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/drivers', methods=['GET'])
def get_drivers():
    """Get all registered drivers"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        drivers = Driver.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return jsonify({
            'success': True,
            'drivers': [driver.to_dict() for driver in drivers.items],
            'total': drivers.total,
            'pages': drivers.pages,
            'current_page': page
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/health', methods=['GET'])
def health():
    """Health check for auth service"""
    try:
        driver_count = Driver.query.count()

        return jsonify({
            'success': True,
            'service': 'authentication',
            'status': 'healthy',
            'total_drivers': driver_count
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500