# Timeline to Office Day Counter

Analyze Google Maps Timeline data to categorize working days for German tax reporting (Entfernungspauschale, Homeoffice-Pauschale, etc.).

## What It Does

Automatically categorizes your working days into:

- **🏢 Office Days** - Visited office location during working hours (Commuter allowance - Entfernungspauschale)
- **🏠 Home Days** - Worked from home (office not visited -> Homeoffice Tagespauschale)
- **🌍 Elsewhere Days** - Worked from other locations (business trips and meal allowances)
- **❓ Missing Data** - Working days without location data

Output includes precise counts and date lists ready for your *Steuererklärung*.

## Quick Start

### Two Analysis Methods

**Option A: `main_simple.py`** (Recommended)
- Uses Google's semantic tags (`WORK`, `HOME`)
- Fast, zero configuration
- Relies on Google's location tagging

**Option B: `main.py`** (Precise Control)  
- GPS coordinate matching with configurable radius
- Full control over location definitions
- Useful when Google tags locations incorrectly

### 1. Export Timeline Data

Export your Google Timeline following [Google's instructions](https://support.google.com/maps/answer/6258979?hl=en&co=GENIE.Platform%3DAndroid&oco=1). Save the JSON file as `Timeline.json` in the project directory.

### 2. Configure & Run

Create a `.env` file with your settings (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your settings:

**For `main_simple.py` (only 2 variables needed):**
```env
CALENDAR_YEAR=2025
WORKING_HOURS=9:00-18:00
```

**For `main.py` (all variables needed):**
```env
CALENDAR_YEAR=2025
WORKING_HOURS=9:00-18:00
TIMEZONE=Europe/Berlin

# Get coordinates by right-clicking in Google Maps
OFFICE_LATITUDE=52.520008
OFFICE_LONGITUDE=13.404954
HOME_LATITUDE=52.516275
HOME_LONGITUDE=13.377704
RADIUS=100
```

Run the analysis:
```bash
python main_simple.py  # Uses Google's semantic tags (recommended)
# or
python main.py         # Uses GPS coordinates
```

## Output Example

```
Expected 261 working days in 2025
Found data for 230 working days

==================================================
         Working Day Analysis
==================================================

🏢 Office Days: 145
   2025-01-07, 2025-01-08, 2025-01-09, ...

🏠 Home Days: 8
   2025-04-21, 2025-06-09, 2025-06-30, ...

🌍 Elsewhere Days: 77
   2025-01-03, 2025-01-06, 2025-01-21, ...

❓ Missing Data Days: 31
   2025-01-01, 2025-01-02, 2025-02-07, ...

==================================================
Total working days with data: 230
Total working days missing data: 31
==================================================
```

## Requirements

- Python 3.6+
- python-dotenv (for loading environment variables from `.env` file)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Important Notes

**⚠️ Not Tax Advice:** This tool provides data analysis only. Always verify results and consult a tax professional (*Steuerberater*) for official advice. The categorization logic may not match your specific tax situation.

**🔒 Privacy:** All processing happens locally on your machine. Your Timeline data never leaves your computer.

**✓ Data Quality:** Review the "Missing Data Days" list. Days without location data require manual verification for accurate tax reporting.

---

*Because if Google knows where you've been, you might as well get a tax deduction.*
*Made with ❤️ in Düsseldorf*
