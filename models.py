from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Driver(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    license_expiry = db.Column(db.Date, nullable=False)
    vehicle_plate = db.Column(db.String(20), nullable=False)
    insurance_provider = db.Column(db.String(100), nullable=False)
    insurance_expiry = db.Column(db.Date, nullable=False)
    road_cert_number = db.Column(db.String(50), nullable=False)
    cert_expiry = db.Column(db.Date, nullable=False)
    blockchain_tx = db.Column(db.String(100))
    wallet_address = db.Column(db.String(42))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'license_number': self.license_number,
            'license_expiry': self.license_expiry.isoformat(),
            'vehicle_plate': self.vehicle_plate,
            'insurance_provider': self.insurance_provider,
            'insurance_expiry': self.insurance_expiry.isoformat(),
            'road_cert_number': self.road_cert_number,
            'cert_expiry': self.cert_expiry.isoformat(),
            'blockchain_tx': self.blockchain_tx,
            'wallet_address': self.wallet_address
        }


class TrafficIncident(db.Model):
    __tablename__ = 'traffic_incidents'

    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    incident_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    casualties = db.Column(db.Integer, default=0)
    time_of_day = db.Column(db.String(20), nullable=False)
    weather_condition = db.Column(db.String(50))
    road_condition = db.Column(db.String(50))
    incident_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'incident_type': self.incident_type,
            'severity': self.severity,
            'casualties': self.casualties,
            'time_of_day': self.time_of_day,
            'weather_condition': self.weather_condition,
            'road_condition': self.road_condition,
            'incident_date': self.incident_date.isoformat()
        }


class RouteAnalysis(db.Model):
    __tablename__ = 'route_analyses'

    id = db.Column(db.Integer, primary_key=True)
    start_location = db.Column(db.String(200), nullable=False)
    end_location = db.Column(db.String(200), nullable=False)
    recommended_route = db.Column(db.String(200))
    congestion_level = db.Column(db.Integer)
    accident_count = db.Column(db.Integer)
    estimated_time = db.Column(db.Integer)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'start_location': self.start_location,
            'end_location': self.end_location,
            'recommended_route': self.recommended_route,
            'congestion_level': self.congestion_level,
            'accident_count': self.accident_count,
            'estimated_time': self.estimated_time,
            'analysis_date': self.analysis_date.isoformat()
        }