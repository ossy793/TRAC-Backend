import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Blueprint, request, jsonify
from models import Driver, db
from services.polygon_service import polygon_service
from datetime import datetime, date

verification_bp = Blueprint('verification', __name__)


@verification_bp.route('/driver', methods=['POST'])
def verify_driver():
    """Verify driver by license number"""
    try:
        data = request.get_json()
        driver_id = data.get('driver_id') or data.get('license_number')

        if not driver_id:
            return jsonify({
                'success': False,
                'error': 'Driver ID or license number required'
            }), 400

        # Search in database
        driver = Driver.query.filter_by(license_number=driver_id).first()

        if not driver:
            return jsonify({
                'success': False,
                'error': 'Driver not found'
            }), 404

        # Get blockchain verification
        blockchain_data = polygon_service.verify_driver(driver.wallet_address)

        # Check document validity
        today = date.today()
        license_valid = driver.license_expiry > today
        insurance_valid = driver.insurance_expiry > today
        cert_valid = driver.cert_expiry > today

        # Prepare response
        return jsonify({
            'success': True,
            'data': {
                'driver_info': {
                    'full_name': f"{driver.first_name} {driver.last_name}",
                    'license_number': driver.license_number,
                    'license_expiry': driver.license_expiry.isoformat(),
                    'license_valid': license_valid,
                    'insurance_number': driver.insurance_provider,
                    'insurance_expiry': driver.insurance_expiry.isoformat(),
                    'insurance_valid': insurance_valid,
                    'vehicle_number': driver.vehicle_plate,
                    'road_worthiness': driver.road_cert_number,
                    'road_worthiness_expiry': driver.cert_expiry.isoformat(),
                    'road_worthiness_valid': cert_valid,
                    'all_documents_valid': license_valid and insurance_valid and cert_valid
                },
                'blockchain_info': {
                    'blockchain_hash': driver.blockchain_tx or 'N/A',
                    'verified_on_chain': bool(driver.blockchain_tx),
                    'wallet_address': driver.wallet_address,
                    'network': 'Polygon Mumbai',
                    'explorer_url': f"https://mumbai.polygonscan.com/tx/{driver.blockchain_tx}" if driver.blockchain_tx else None
                },
                'verified_at': datetime.now().isoformat()
            }
        }), 200

    except Exception as e:
        print(f"Error in verify_driver: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Verification failed: {str(e)}"
        }), 500


@verification_bp.route('/wallet/<wallet_address>', methods=['GET'])
def verify_by_wallet(wallet_address):
    """Verify driver by wallet address"""
    try:
        driver = Driver.query.filter_by(wallet_address=wallet_address).first()

        if not driver:
            return jsonify({
                'success': False,
                'error': 'No driver found for this wallet'
            }), 404

        # Get blockchain verification
        blockchain_data = polygon_service.verify_driver(wallet_address)

        # Check document validity
        today = date.today()
        license_valid = driver.license_expiry > today
        insurance_valid = driver.insurance_expiry > today
        cert_valid = driver.cert_expiry > today

        return jsonify({
            'success': True,
            'data': {
                'driver_info': {
                    'full_name': f"{driver.first_name} {driver.last_name}",
                    'license_number': driver.license_number,
                    'license_expiry': driver.license_expiry.isoformat(),
                    'license_valid': license_valid,
                    'insurance_number': driver.insurance_provider,
                    'insurance_expiry': driver.insurance_expiry.isoformat(),
                    'insurance_valid': insurance_valid,
                    'vehicle_number': driver.vehicle_plate,
                    'road_worthiness': driver.road_cert_number,
                    'road_worthiness_expiry': driver.cert_expiry.isoformat(),
                    'road_worthiness_valid': cert_valid,
                    'all_documents_valid': license_valid and insurance_valid and cert_valid
                },
                'blockchain_info': {
                    'blockchain_hash': driver.blockchain_tx or 'N/A',
                    'verified_on_chain': bool(driver.blockchain_tx),
                    'wallet_address': driver.wallet_address,
                    'network': 'Polygon Mumbai'
                },
                'blockchain_data': blockchain_data
            }
        }), 200

    except Exception as e:
        print(f"Error in verify_by_wallet: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Verification failed: {str(e)}"
        }), 500


@verification_bp.route('/check-validity/<license_number>', methods=['GET'])
def check_validity(license_number):
    """Check document validity by license number"""
    try:
        driver = Driver.query.filter_by(license_number=license_number).first()

        if not driver:
            return jsonify({
                'success': False,
                'error': 'Driver not found'
            }), 404

        today = date.today()
        license_valid = driver.license_expiry > today
        insurance_valid = driver.insurance_expiry > today
        cert_valid = driver.cert_expiry > today

        return jsonify({
            'success': True,
            'data': {
                'valid': license_valid and insurance_valid and cert_valid,
                'license_status': 'VALID' if license_valid else 'EXPIRED',
                'insurance_status': 'ACTIVE' if insurance_valid else 'EXPIRED',
                'road_worthiness': 'VALID' if cert_valid else 'EXPIRED',
                'license_expiry': driver.license_expiry.isoformat(),
                'insurance_expiry': driver.insurance_expiry.isoformat(),
                'cert_expiry': driver.cert_expiry.isoformat(),
                'days_until_license_expiry': (driver.license_expiry - today).days,
                'days_until_insurance_expiry': (driver.insurance_expiry - today).days,
                'days_until_cert_expiry': (driver.cert_expiry - today).days
            }
        }), 200

    except Exception as e:
        print(f"Error in check_validity: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Validity check failed: {str(e)}"
        }), 500


@verification_bp.route('/blockchain-status', methods=['GET'])
def blockchain_status():
    """Get blockchain connection status"""
    try:
        network_info = polygon_service.get_network_info()

        return jsonify({
            'success': True,
            'blockchain': 'Polygon',
            'network': network_info.get('network'),
            'connected': network_info.get('connected'),
            'chain_id': network_info.get('chain_id'),
            'rpc_url': network_info.get('rpc_url')
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@verification_bp.route('/health', methods=['GET'])
def health():
    """Health check for verification service"""
    try:
        driver_count = Driver.query.count()

        return jsonify({
            'success': True,
            'service': 'verification',
            'status': 'healthy',
            'database': 'connected',
            'total_drivers': driver_count,
            'blockchain_service': 'active'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500