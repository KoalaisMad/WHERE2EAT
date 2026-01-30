# WHERE2EAT

A web application that helps you find the perfect restaurant based on your preferences, location, budget, time constraints, and dietary restrictions.

## Features

- **Location-based search**: Uses GPS or manual zipcode entry to find nearby restaurants
- **Smart filtering**: Filters restaurants by:
  - Budget range ($, $$, $$$, $$$$)
  - Time available (accounts for round-trip travel time)
  - Transportation mode (walking, biking, driving, public transport)
  - Cuisine preference
  - Dietary restrictions (vegan, vegetarian, halal, kosher, gluten-free, etc.)
- **Random selection**: Randomly picks from restaurants that match your criteria
- **Google Maps integration**: Get directions directly to your selected restaurant
- **Multiple options**: View all matching restaurants or pick another random option

## Setup

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/WHERE2EAT.git
cd WHERE2EAT
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python mainLogic.py
```

4. Open your browser and navigate to:
```
http://localhost:8080
```

## Usage

1. Click "Get Started" on the splash screen
2. Fill in your preferences:
   - Budget Range
   - Time Available for Commute
   - Transportation method
   - Cuisine Preference
   - Dietary Restrictions (optional)
   - Your Location (GPS or manual entry)
3. Click "Find My Perfect Restaurant"
4. View your restaurant recommendation
5. Use "Get Directions" to open Google Maps
6. Use "Pick Another" to see a different option
7. Use "View All Options" to see all matching restaurants

## How It Works

- **Location**: Uses Overpass API to find restaurants near your location
- **Travel Time**: Uses OSRM (Open Source Routing Machine) to calculate travel times based on your transportation mode
- **Filtering**: Applies all your preferences to narrow down restaurant options
- **Randomization**: Randomly selects from restaurants that meet all criteria

## API Endpoints

- `GET /` - Serves the main HTML page
- `POST /location` - Receives GPS coordinates from the frontend
- `POST /find-restaurant` - Finds restaurants based on user preferences

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **APIs**: 
  - Overpass API (OpenStreetMap) - Restaurant data
  - OSRM - Route calculation
  - Zippopotam - Zipcode to coordinates
  - Google Maps - Directions

## Deployment

### Option 1: Render (Recommended)

1. Push your code to GitHub
2. Go to [Render.com](https://render.com)
3. Create a new Web Service
4. Connect your GitHub repository
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `python mainLogic.py`
7. Deploy!

### Option 2: Heroku

1. Install Heroku CLI
2. Create a `Procfile` with: `web: python mainLogic.py`
3. Run:
```bash
heroku create your-app-name
git push heroku main
```

### Option 3: PythonAnywhere

1. Upload files via web interface
2. Configure web app to run `mainLogic.py`
3. Set up static files mapping

## File Structure

```
WHERE2EAT/
├── mainLogic.py          # Flask backend server
├── location.html         # Frontend HTML/CSS/JavaScript
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .gitignore           # Git ignore rules
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.
