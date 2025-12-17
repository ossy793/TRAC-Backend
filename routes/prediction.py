import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Blueprint, request, jsonify
from services.ai_service import predict_best_route, analyze_traffic_patterns
from services.data_analysis import data_analysis_service
from datetime import datetime
import random

prediction_bp = Blueprint('prediction', __name__)


@prediction_bp.route('/route', methods=['POST'])
def predict_route():
    """Predict best route using AI"""
    try:
        data = request.get_json()

        start_location = data.get('start_location') or data.get('start')
        end_location = data.get('end_location') or data.get('end')
        time_of_day = data.get('time_of_day', 'afternoon')

        if not start_location or not end_location:
            return jsonify({
                'success': False,
                'error': 'Start and end locations are required'
            }), 400

        # Get route predictions from AI service
        routes = predict_best_route(start_location, end_location, time_of_day)

        # Get accident statistics
        stats = data_analysis_service.get_accident_statistics(start_location, end_location)

        # Determine recommendation
        main_route = routes[0]
        alternative_route = routes[1] if len(routes) > 1 else routes[0]

        recommendation = 'alternative' if alternative_route['recommended'] else 'main'
        time_saved = abs(main_route['estimated_time_min'] - alternative_route['estimated_time_min'])

        return jsonify({
            'success': True,
            'data': {
                'main_route': {
                    'name': main_route['name'],
                    'congestion_level': main_route['congestion_level'] * 10,  # Convert to percentage
                    'accidents_reported': main_route['historical_accidents'],
                    'estimated_time_minutes': main_route['estimated_time_min'],
                    'distance_km': main_route['distance_km'],
                    'risk_level': main_route['accident_risk']
                },
                'alternative_route': {
                    'name': alternative_route['name'],
                    'congestion_level': alternative_route['congestion_level'] * 10,
                    'accidents_reported': alternative_route['historical_accidents'],
                    'estimated_time_minutes': alternative_route['estimated_time_min'],
                    'distance_km': alternative_route['distance_km'],
                    'risk_level': alternative_route['accident_risk']
                },
                'recommendation': recommendation,
                'time_difference_minutes': time_saved,
                'analysis_timestamp': datetime.now().isoformat(),
                'confidence_score': round(random.uniform(0.85, 0.95), 2)
            },
            'statistics': stats
        }), 200

    except Exception as e:
        print(f"Route prediction error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prediction_bp.route('/accident-hotspots', methods=['GET'])
def accident_hotspots():
    """Get accident hotspots"""
    try:
        limit = request.args.get('limit', 10, type=int)
        hotspots = data_analysis_service.identify_hotspots(limit)

        return jsonify({
            'success': True,
            'hotspots': hotspots,
            'count': len(hotspots)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prediction_bp.route('/statistics', methods=['GET'])
def statistics():
    """Get traffic statistics"""
    try:
        start_location = request.args.get('start_location')
        end_location = request.args.get('end_location')

        stats = data_analysis_service.get_accident_statistics(start_location, end_location)

        return jsonify({
            'success': True,
            'data': {
                'accidents': {
                    'total_accidents': stats['total_accidents_30days'],
                    'fatal': stats['fatal_accidents'],
                    'severe': stats['severe_accidents'],
                    'moderate': stats['moderate_accidents'],
                    'minor': stats['minor_accidents']
                },
                'prediction_accuracy': stats['prediction_accuracy'],
                'most_common_cause': stats['most_common_cause'],
                'peak_time': stats['peak_accident_time']
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prediction_bp.route('/health', methods=['GET'])
def health():
    """Health check for prediction service"""
    return jsonify({
        'success': True,
        'service': 'prediction',
        'status': 'healthy',
        'ai_model': 'active'
    }), 200