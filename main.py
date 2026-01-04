import json
import os
from datetime import datetime
from dotenv import load_dotenv
from utils import (
    haversine_distance,
    parse_latlng,
    is_within_working_hours,
    is_working_day,
    get_year_from_timestamp,
    get_all_working_days_in_year
)

# Load environment variables from .env file
load_dotenv()

### CONFIGURATION
CALENDAR_YEAR = int(os.getenv('CALENDAR_YEAR', '2025'))
TIMELINE_FILE = "Timeline.json"
WORKING_HOURS = os.getenv('WORKING_HOURS', '9:00-18:00')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Berlin')
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

### Location data - loaded from .env file
OFFICE_LATITUDE = float(os.getenv('OFFICE_LATITUDE', '52.520008'))
OFFICE_LONGITUDE = float(os.getenv('OFFICE_LONGITUDE', '13.404954'))
HOME_LATITUDE = float(os.getenv('HOME_LATITUDE', '52.516275'))
HOME_LONGITUDE = float(os.getenv('HOME_LONGITUDE', '13.377704'))
RADIUS = int(os.getenv('RADIUS', '100'))


def categorize_days(timeline_file, config):
    """Main analysis logic to categorize working days."""
    print(f"Loading Timeline data from {timeline_file}...")
    
    with open(timeline_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = data.get('semanticSegments', [])
    print(f"Found {len(segments)} timeline segments")
    
    calendar_year = config.get('calendar_year')
    
    # Get all possible working days in the year
    all_possible_working_days = set()
    if calendar_year:
        all_possible_working_days = get_all_working_days_in_year(
            calendar_year, 
            config['days_of_week']
        )
        print(f"Expected {len(all_possible_working_days)} working days in {calendar_year}")
    
    # Track which days had office/home visits and which days have ANY data
    office_days = set()
    home_days = set()
    days_with_data = set()
    days_with_working_hour_visits = set()  # Days with visits during 9:00-20:00
    
    # Track minimum distance from home/office for each day (for elsewhere breakdown)
    day_min_distances = {}
    
    segments_processed = 0
    segments_skipped = 0
    
    for segment in segments:
        # Check if this is a visit segment
        if 'visit' not in segment:
            continue
        
        start_time = segment.get('startTime', '')
        end_time = segment.get('endTime', '')
        
        if not start_time:
            continue
        
        # Filter by calendar year if specified
        if calendar_year:
            year = get_year_from_timestamp(start_time)
            if year != calendar_year:
                segments_skipped += 1
                continue
        
        segments_processed += 1
        
        # Get the date for this segment
        try:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except:
            continue
        
        # Check if it's a working day
        if not is_working_day(start_time, config['days_of_week']):
            continue
        
        # Mark that this working day has data
        days_with_data.add(date_str)
        
        # Check if within working hours
        if not is_within_working_hours(start_time, config['working_hours']):
            continue
        
        # Mark that this day has visits during working hours
        days_with_working_hour_visits.add(date_str)
        
        # Get location from visit
        visit = segment.get('visit', {})
        top_candidate = visit.get('topCandidate', {})
        place_location = top_candidate.get('placeLocation', {})
        latlng = place_location.get('latLng', '')
        
        if not latlng:
            continue
        
        lat, lng = parse_latlng(latlng)
        if lat is None or lng is None:
            continue
        
        # Calculate distance to office
        office_distance = haversine_distance(
            lat, lng,
            config['office_lat'], config['office_lng']
        )
        
        # Calculate distance to home
        home_distance = haversine_distance(
            lat, lng,
            config['home_lat'], config['home_lng']
        )
        
        # Track minimum distance from home or office for this day
        min_distance = min(office_distance, home_distance)
        if date_str not in day_min_distances or min_distance < day_min_distances[date_str]:
            day_min_distances[date_str] = min_distance
        
        # Categorize
        if office_distance <= config['radius']:
            office_days.add(date_str)
        elif home_distance <= config['radius']:
            home_days.add(date_str)
    
    # Calculate day categories
    home_only_days = home_days - office_days
    
    # Elsewhere days = days with working hour visits that are not office or home
    elsewhere_days = days_with_working_hour_visits - office_days - home_only_days
    
    # Missing days includes:
    # 1. Working days with no location data at all
    # 2. Working days with data but no visits during working hours
    missing_days = set()
    if calendar_year:
        missing_days = all_possible_working_days - days_with_working_hour_visits
    
    # Calculate distance breakdown for elsewhere days
    elsewhere_breakdown = {
        'local': [],        # < 50km
        'regional': [],     # 50-150km
        'national': [],     # 150-500km
        'international': []  # > 500km
    }
    
    for day in elsewhere_days:
        if day in day_min_distances:
            distance_km = day_min_distances[day] / 1000  # Convert to km
            if distance_km < 50:
                elsewhere_breakdown['local'].append(day)
            elif distance_km < 150:
                elsewhere_breakdown['regional'].append(day)
            elif distance_km < 500:
                elsewhere_breakdown['national'].append(day)
            else:
                elsewhere_breakdown['international'].append(day)
    
    print(f"Processed {segments_processed} segments from {calendar_year or 'all years'}")
    if segments_skipped > 0:
        print(f"Skipped {segments_skipped} segments from other years")
    print(f"Found data for {len(days_with_data)} working days")
    
    return {
        'office': sorted(office_days),
        'home': sorted(home_only_days),
        'elsewhere': sorted(elsewhere_days),
        'elsewhere_breakdown': elsewhere_breakdown,
        'missing': sorted(missing_days)
    }


def display_results(results):
    """Display results in a clean, formatted way."""
    print("\n" + "="*50)
    print("         Working Day Analysis")
    print("="*50 + "\n")
    
    print(f"🏢 Office Days: {len(results['office'])}")
    if results['office']:
        print("   " + ", ".join(results['office'][:10]))
        if len(results['office']) > 10:
            print(f"   ... and {len(results['office']) - 10} more")
    print()
    
    print(f"🏠 Home Days: {len(results['home'])}")
    if results['home']:
        print("   " + ", ".join(results['home'][:10]))
        if len(results['home']) > 10:
            print(f"   ... and {len(results['home']) - 10} more")
    print()
    
    print(f"🌍 Elsewhere Days: {len(results['elsewhere'])}")
    
    # Show distance breakdown if available
    if 'elsewhere_breakdown' in results:
        breakdown = results['elsewhere_breakdown']
        
        local = breakdown['local']
        if local:
            print(f"   Local (< 50km): {len(local)} days")
            if len(local) <= 5:
                print("      " + ", ".join(local))
            else:
                print("      " + ", ".join(local[:5]) + f" ... and {len(local) - 5} more")
        
        regional = breakdown['regional']
        if regional:
            print(f"   Regional (50-150km): {len(regional)} days")
            if len(regional) <= 5:
                print("      " + ", ".join(regional))
            else:
                print("      " + ", ".join(regional[:5]) + f" ... and {len(regional) - 5} more")
        
        national = breakdown['national']
        if national:
            print(f"   National (150-500km): {len(national)} days")
            if len(national) <= 5:
                print("      " + ", ".join(national))
            else:
                print("      " + ", ".join(national[:5]) + f" ... and {len(national) - 5} more")
        
        international = breakdown['international']
        if international:
            print(f"   International (500km+): {len(international)} days")
            if len(international) <= 5:
                print("      " + ", ".join(international))
            else:
                print("      " + ", ".join(international[:5]) + f" ... and {len(international) - 5} more")
    elif results['elsewhere']:
        print("   " + ", ".join(results['elsewhere'][:10]))
        if len(results['elsewhere']) > 10:
            print(f"   ... and {len(results['elsewhere']) - 10} more")
    print()
    
    print(f"❓ Missing Data Days: {len(results['missing'])}")
    if results['missing']:
        print("   " + ", ".join(results['missing'][:10]))
        if len(results['missing']) > 10:
            print(f"   ... and {len(results['missing']) - 10} more")
    print()
    
    print("="*50)
    total_with_data = len(results['office']) + len(results['home']) + len(results['elsewhere'])
    print(f"Total working days with data: {total_with_data}")
    print(f"Total working days missing data: {len(results['missing'])}")
    print("="*50 + "\n")


def main():
    """Main entry point."""
    config = {
        'calendar_year': CALENDAR_YEAR,
        'working_hours': WORKING_HOURS,
        'days_of_week': DAYS_OF_WEEK,
        'office_lat': OFFICE_LATITUDE,
        'office_lng': OFFICE_LONGITUDE,
        'home_lat': HOME_LATITUDE,
        'home_lng': HOME_LONGITUDE,
        'radius': RADIUS
    }
    
    results = categorize_days(TIMELINE_FILE, config)
    display_results(results)


if __name__ == "__main__":
    main()












