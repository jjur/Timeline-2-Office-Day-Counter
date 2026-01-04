"""
Utility functions for Timeline analysis.
"""
import math
from datetime import datetime


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters using Haversine formula."""
    R = 6371000  # Earth radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def parse_latlng(latlng_string):
    """Parse lat/lng string like '49.2104132°, 19.2868596°' to tuple of floats."""
    try:
        parts = latlng_string.replace('°', '').split(',')
        lat = float(parts[0].strip())
        lng = float(parts[1].strip())
        return lat, lng
    except:
        return None, None


def is_within_working_hours(timestamp_str, working_hours):
    """Check if timestamp falls within working hours."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        time = dt.time()
        
        start_str, end_str = working_hours.split('-')
        start_hour, start_min = map(int, start_str.split(':'))
        end_hour, end_min = map(int, end_str.split(':'))
        
        start_time = datetime.strptime(f"{start_hour:02d}:{start_min:02d}", "%H:%M").time()
        end_time = datetime.strptime(f"{end_hour:02d}:{end_min:02d}", "%H:%M").time()
        
        return start_time <= time <= end_time
    except:
        return False


def is_working_day(timestamp_str, days_of_week):
    """Check if timestamp falls on a working day."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        day_name = dt.strftime('%A')
        return day_name in days_of_week
    except:
        return False


def get_year_from_timestamp(timestamp_str):
    """Extract year from timestamp string."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.year
    except:
        return None


def get_all_working_days_in_year(year, days_of_week):
    """Generate all working days in a given year."""
    from datetime import date, timedelta
    
    working_days = set()
    current_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    while current_date <= end_date:
        if current_date.strftime('%A') in days_of_week:
            working_days.add(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    return working_days

