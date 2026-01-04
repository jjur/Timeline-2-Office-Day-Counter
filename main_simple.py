"""
Simplified Timeline analyzer using Google's built-in semantic location tags.
No coordinate calculations needed - uses WORK/HOME tags directly from Timeline.
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from utils import (
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
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Semantic types that count as office/work
WORK_TYPES = {"WORK", "INFERRED_WORK"}

# Semantic types that count as home
HOME_TYPES = {"HOME", "INFERRED_HOME"}


def categorize_days_simple(timeline_file, config):
    """Main analysis logic using built-in semantic tags."""
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
    
    segments_processed = 0
    segments_skipped = 0
    
    for segment in segments:
        # Check if this is a visit segment
        if 'visit' not in segment:
            continue
        
        start_time = segment.get('startTime', '')
        
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
        
        # Get semantic type from visit
        visit = segment.get('visit', {})
        top_candidate = visit.get('topCandidate', {})
        semantic_type = top_candidate.get('semanticType', '')
        
        if not semantic_type:
            continue
        
        # Categorize based on semantic type
        if semantic_type in config['work_types']:
            office_days.add(date_str)
        elif semantic_type in config['home_types']:
            home_days.add(date_str)
    
    # Calculate day categories
    home_only_days = home_days - office_days
    elsewhere_days = days_with_data - office_days - home_only_days
    
    # Calculate missing days (working days with no location data)
    missing_days = set()
    if calendar_year:
        missing_days = all_possible_working_days - days_with_data
    
    print(f"Processed {segments_processed} segments from {calendar_year or 'all years'}")
    if segments_skipped > 0:
        print(f"Skipped {segments_skipped} segments from other years")
    print(f"Found data for {len(days_with_data)} working days")
    
    return {
        'office': sorted(office_days),
        'home': sorted(home_only_days),
        'elsewhere': sorted(elsewhere_days),
        'missing': sorted(missing_days)
    }


def display_results(results):
    """Display results in a clean, formatted way."""
    print("\n" + "="*50)
    print("    Working Day Analysis (Semantic Tags)")
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
    if results['elsewhere']:
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
        'work_types': WORK_TYPES,
        'home_types': HOME_TYPES
    }
    
    results = categorize_days_simple(TIMELINE_FILE, config)
    display_results(results)


if __name__ == "__main__":
    main()

