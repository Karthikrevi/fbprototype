
import math
from typing import Optional, Dict, List

# Kerala district codes mapping
KERALA_DISTRICTS = {
    'TVM': 'Thiruvananthapuram',
    'KLM': 'Kollam',
    'PTA': 'Pathanamthitta',
    'ALP': 'Alappuzha',
    'KTM': 'Kottayam',
    'IDK': 'Idukki',
    'EKM': 'Ernakulam',
    'TSR': 'Thrissur',
    'PKD': 'Palakkad',
    'MPM': 'Malappuram',
    'KZD': 'Kozhikode',
    'WYD': 'Wayanad',
    'KNR': 'Kannur',
    'KSD': 'Kasaragod'
}

# Sample ward data (in production, this would come from a proper GIS database)
SAMPLE_WARDS = {
    'TVM': [
        {'id': 'TVM001', 'name': 'Pazhavangadi', 'lat': 8.5241, 'lng': 76.9366},
        {'id': 'TVM002', 'name': 'Fort', 'lat': 8.5077, 'lng': 76.9478},
        {'id': 'TVM003', 'name': 'Palayam', 'lat': 8.5137, 'lng': 76.9446},
        {'id': 'TVM004', 'name': 'Chalai', 'lat': 8.5030, 'lng': 76.9553},
        {'id': 'TVM005', 'name': 'Vellayambalam', 'lat': 8.5386, 'lng': 76.9264},
    ],
    'EKM': [
        {'id': 'EKM001', 'name': 'Marine Drive', 'lat': 9.9312, 'lng': 76.2673},
        {'id': 'EKM002', 'name': 'Ernakulam South', 'lat': 9.9816, 'lng': 76.2999},
        {'id': 'EKM003', 'name': 'Fort Kochi', 'lat': 9.9654, 'lng': 76.2424},
    ],
    'KZD': [
        {'id': 'KZD001', 'name': 'Kozhikode Beach', 'lat': 11.2588, 'lng': 75.7804},
        {'id': 'KZD002', 'name': 'SM Street', 'lat': 11.2504, 'lng': 75.7703},
    ]
}

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng / 2) * math.sin(delta_lng / 2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def find_nearest_ward(lat: float, lng: float, district_code: str = 'TVM') -> Optional[Dict]:
    """Find nearest ward based on coordinates"""
    if district_code not in SAMPLE_WARDS:
        return None
    
    wards = SAMPLE_WARDS[district_code]
    nearest_ward = None
    min_distance = float('inf')
    
    for ward in wards:
        distance = calculate_distance(lat, lng, ward['lat'], ward['lng'])
        if distance < min_distance:
            min_distance = distance
            nearest_ward = ward.copy()
            nearest_ward['distance'] = distance
    
    return nearest_ward

def validate_coordinates(lat: float, lng: float, accuracy: float = None) -> Dict:
    """Validate GPS coordinates and check for potential spoofing"""
    result = {
        'valid': True,
        'within_kerala': False,
        'accuracy_acceptable': True,
        'warnings': []
    }
    
    # Basic coordinate validation
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        result['valid'] = False
        result['warnings'].append('Invalid coordinates')
        return result
    
    # Kerala bounding box (approximate)
    kerala_bounds = {
        'min_lat': 8.1777,
        'max_lat': 12.7839,
        'min_lng': 74.8520,
        'max_lng': 77.4072
    }
    
    if (kerala_bounds['min_lat'] <= lat <= kerala_bounds['max_lat'] and
        kerala_bounds['min_lng'] <= lng <= kerala_bounds['max_lng']):
        result['within_kerala'] = True
    else:
        result['warnings'].append('Coordinates outside Kerala')
    
    # Accuracy check (if provided)
    if accuracy is not None:
        if accuracy > 100:  # More than 100m accuracy
            result['accuracy_acceptable'] = False
            result['warnings'].append('Low GPS accuracy')
        
        if accuracy == 0:  # Suspicious - perfect accuracy
            result['warnings'].append('Suspicious GPS accuracy')
    
    return result

def get_district_from_coordinates(lat: float, lng: float) -> Optional[str]:
    """Get district code from coordinates (simplified implementation)"""
    # This is a simplified implementation
    # In production, use proper GIS polygon intersection
    
    # Thiruvananthapuram district bounds (approximate)
    if 8.1777 <= lat <= 8.7 and 76.7 <= lng <= 77.4:
        return 'TVM'
    
    # Ernakulam district bounds (approximate)  
    if 9.7 <= lat <= 10.3 and 76.0 <= lng <= 76.8:
        return 'EKM'
    
    # Kozhikode district bounds (approximate)
    if 11.0 <= lat <= 11.6 and 75.5 <= lng <= 76.2:
        return 'KZD'
    
    # Default to TVM if within Kerala but district not identified
    kerala_bounds = {
        'min_lat': 8.1777,
        'max_lat': 12.7839,
        'min_lng': 74.8520,
        'max_lng': 77.4072
    }
    
    if (kerala_bounds['min_lat'] <= lat <= kerala_bounds['max_lat'] and
        kerala_bounds['min_lng'] <= lng <= kerala_bounds['max_lng']):
        return 'TVM'  # Default district
    
    return None

def get_ward_list(district_code: str) -> List[Dict]:
    """Get list of wards for a district"""
    return SAMPLE_WARDS.get(district_code, [])

def format_location_display(lat: float, lng: float, ward_id: str = None) -> str:
    """Format location for display"""
    if ward_id:
        # Find ward details
        for district, wards in SAMPLE_WARDS.items():
            for ward in wards:
                if ward['id'] == ward_id:
                    return f"{ward['name']}, {KERALA_DISTRICTS.get(district, district)}"
    
    # Fallback to coordinates
    return f"{lat:.4f}, {lng:.4f}"

def get_location_stats(district_code: str = None) -> Dict:
    """Get location-based statistics"""
    # This would typically query the database
    # For now, return sample data
    return {
        'total_animals': 150,
        'by_district': {
            'TVM': 45,
            'EKM': 38,
            'KZD': 25,
            'Others': 42
        },
        'by_type': {
            'strays': 89,
            'pets': 61
        }
    }
