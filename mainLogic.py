# Inputs: Location, time, budget, allotted time, cuisine preferred, mode of transport
# For walking take everything within 5km radius
# For biking 10km and for driving - 30km
# These increase/decrease based on time
# Output: one restaurant
# Will randomize the chosen one based on the restaurants that meet the requirements

# Get all the restaurants based on location 
# Create a csv 
from datetime import datetime
from urllib import response
from flask import Flask, request, jsonify, render_template_string, send_from_directory
import pandas as pd
import requests
import random
import os
import re

app = Flask(__name__)

try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    print("flask-cors not installed, continuing without CORS support")

currentTime = ""

# getting latitude and longitude from zipcode
def zipToLatlon(zipCode):
        url = f"https://api.zippopotam.us/us/{zipCode}"
        try:
             r = requests.get(url, timeout=10)
             r.raise_for_status()
             data = r.json()
             if "places" in data and len(data["places"]) > 0:
                place = data["places"][0]
                lat = float(place["latitude"])
                lon = float(place["longitude"])
                return lat, lon 
        except (requests.exceptions.RequestException, KeyError, IndexError, ValueError) as e:
             print(f"Error in getting latitude and longitude from zippopotam: {e}")
             pass

# getting all the nearby restaurants using longitude and latitude
def nearbyRestaurants(latitude, longitude, radius=1500):
        overpassUrl = "https://overpass-api.de/api/interpreter"
        query = f"""[out:json];(
        node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
        way["amenity"="restaurant"](around:{radius},{latitude},{longitude});
        relation["amenity"="restaurant"](around:{radius},{latitude},{longitude});
        );

        (
        node["amenity"="fast_food"](around:{radius},{latitude},{longitude});
        way["amenity"="fast_food"](around:{radius},{latitude},{longitude});
        relation["amenity"="fast_food"](around:{radius},{latitude},{longitude});
        );
        out center tags;
        """

        response = requests.post(overpassUrl, data=query)
        if response.status_code == 200:
                try:
                      data = response.json()
                except ValueError:
                      print("Error: Response content is not valid JSON from Overpass API.")
                      return []
        else:
                print(f"Error: Overpass API returned status code {response.status_code}")
                return []

        restaurants = []
        for el in data.get("elements", []):
                tags = el.get("tags", {})
                restaurants.append({
                    "name": tags.get("name", "Unknown"),
                    "cuisine": tags.get("cuisine", "N/A"),
                    "lat": el.get("lat") or el.get("center", {}).get("lat"),
                    "lon": el.get("lon") or el.get("center", {}).get("lon"),
                    "address": tags.get("addr:street", ""),
                    "city": tags.get("addr:city", ""),
                    "price_range": tags.get("price_range", "N/A"),
                    "rating": tags.get("rating", "N/A"),
                    "diet_vegan": tags.get("diet:vegan", ""),
                    "diet_vegetarian": tags.get("diet:vegetarian", ""),
                    "diet_halal": tags.get("diet:halal", ""),
                    "diet_kosher": tags.get("diet:kosher", ""),
                    "diet_gluten_free": tags.get("diet:gluten_free", ""),
                    "diet_nut_free": tags.get("diet:nut_free", ""),
                    "diet_dairy_free": tags.get("diet:dairy_free", ""),
                    "dietary_tags": tags.get("dietary", "").lower() if tags.get("dietary") else ""
                })

        return restaurants

# Calculating ETA using OSRM
OSRM_BASE = "https://router.project-osrm.org"

def osrmProfile(mode: str) -> str:
      mode = mode.lower()
      if mode == "walking":
            return "foot"
      if mode == "biking":
            return "bike"
      return "driving"

def etaSecondsToMany(originLat, originLon, destinations, mode="driving"):
      mode = mode.lower()
      if mode == "walking":
            profile = "foot"
      elif mode == "biking":
            profile =  "bike"
      else:
        profile =  "driving"
      
      coord = [f"{originLon},{originLat}"] + [f"{lon},{lat}" for lat, lon in destinations]
      coordStr = ";".join(coord)
      url = f"{OSRM_BASE}/table/v1/{profile}/{coordStr}"
      params = {
        "sources": "0",       
        "destinations": "all",  
        "annotations": "duration"
      }
      r = requests.get(url, params=params, timeout=30)
      r.raise_for_status()
      data = r.json()
      durations = data["durations"][0] 
      return durations[1:]


def filterByTime(restaurants, ilat, ilon, allottedMinutes, mode="driving"):
      dests = [(r["lat"], r["lon"]) for r in restaurants]
      etas = etaSecondsToMany(ilat, ilon, dests, mode=mode)
      # Split time in half for round trip (going there and coming back)
      oneWayMinutes = allottedMinutes / 2
      maxSec = oneWayMinutes * 60
      filtered = []
      for r, eta in zip(restaurants, etas):
        if eta is None:
            continue
        if eta <= maxSec:
            r2 = dict(r)
            r2["eta_minutes"] = round(eta / 60, 1)
            filtered.append(r2)
      filtered.sort(key=lambda x: x["eta_minutes"])
      return filtered

def main():
     lat = 0.0
     lon = 0.0
     
     currentTime = datetime.now().strftime("%H:%M")
     
     budget =  float(input("Enter your budget for the meal: "))
     if(budget <=0):
         print("Invalid budget entered")

          
     allottedTime = float(input("Enter your allotted time in minutes: "))
     if(allottedTime <=0):
            print("Invalid time entered")
      
     CuisinesAvailable = {"italian": True, "chinese": True, "mexican": True, "indian": True, "american": True, "thai": True, "japanese": True, "mediterranean": True}
     print("Available Cuisines:")
     for cuisine in CuisinesAvailable:
         print(cuisine)
     cuisinePreferred =  input("Choose your preferred cuisine: ")
     if(cuisinePreferred.lower() not in CuisinesAvailable):
          print("Invalid cuisine selected")


     modeOfTransport =  input("Enter your mode of transport (walking, biking, driving): ")
     if (modeOfTransport.lower() not in ["walking", "biking", "driving"]):
              print("Invalid mode of transport selected")


     healthy =  input("Do you prefer healthy options? (y for yes/d for doesn't matter): ")
     if (healthy.lower() not in ["y", "d"]):
            print("Invalid healthy preference selected")
          

     Restrictions = ["1. No Beef", "2. Vegan", "3. Vegetarian", "4. Gluten-Free", "5. Nut-Free", "6. Dairy-Free", "7. Halal", "8. Kosher", "9. None"]
     for restriction in Restrictions:
          print(restriction)
     DietaryRestrictions =  int(input("Enter any dietary restrictions from the following options (separate by comma if multiple) by number: "))
     if (DietaryRestrictions <1 or DietaryRestrictions >9):
          print("Invalid dietary restriction selected")

     zipcode = input("Enter your zipcode: ")
     if (len(zipcode) != 5 or not zipcode.isdigit()):
          print("Invalid zipcode entered")

     lat, lon = zipToLatlon(zipcode)
     
     print("Current Time:", currentTime)
     print("Budget:", budget)
     print("Allotted Time (minutes):", allottedTime)
     print("Preferred Cuisine:", cuisinePreferred)
     print("Mode of Transport:", modeOfTransport)
     print("Healthy Preference:", healthy)
     print("Dietary Restrictions:", DietaryRestrictions)
     print(lat, lon)
     restaurantsAvailable = nearbyRestaurants(lat, lon)


     # create a csv of all the restaurants available
     df = pd.DataFrame(restaurantsAvailable)
     df.to_csv("restaurants_available.csv", index=False)
     # clean up the data and print dataframe the whole table
     print(df)

# Flask Routes
@app.route('/')
def home():
    return send_from_directory('.', 'location.html')

# Store user location globally (in production, use session or database)
userLocation = {'lat': None, 'lon': None}

@app.route('/location', methods=['POST'])
def receiveLocation():
    try:
        data = request.json
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')
        
        if latitude and longitude:
            userLocation['lat'] = float(latitude)
            userLocation['lon'] = float(longitude)
        
        print(f"Received location: Lat {latitude}, Lon {longitude}, Accuracy: {accuracy}m")
        
        return jsonify({
            'status': 'success',
            'message': 'Location received successfully',
            'latitude': latitude,
            'longitude': longitude
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

def parseLocationString(locationStr):
    if not locationStr:
        print("parseLocationString: Empty location string")
        return None, None
    
    print(f"parseLocationString: Parsing '{locationStr}'")
    
    coordMatch = re.search(r'\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)', locationStr)
    if coordMatch:
        try:
            lat = float(coordMatch.group(1))
            lon = float(coordMatch.group(2))
            print(f"parseLocationString: Found coordinates: lat={lat}, lon={lon}")
            return lat, lon
        except ValueError as e:
            print(f"parseLocationString: Error parsing coordinates: {e}")
            pass
    
    zipMatch = re.search(r'\b(\d{5})\b', locationStr)
    if zipMatch:
        zipcode = zipMatch.group(1)
        print(f"parseLocationString: Found zipcode: {zipcode}")
        coords = zipToLatlon(zipcode)
        if coords:
            print(f"parseLocationString: Converted zipcode to coordinates: {coords}")
            return coords
        else:
            print(f"parseLocationString: Failed to convert zipcode {zipcode} to coordinates")
    
    if locationStr.strip().isdigit() and len(locationStr.strip()) == 5:
        zipcode = locationStr.strip()
        print(f"parseLocationString: String is a zipcode: {zipcode}")
        coords = zipToLatlon(zipcode)
        if coords:
            print(f"parseLocationString: Converted zipcode to coordinates: {coords}")
            return coords
    
    print(f"parseLocationString: Could not parse location string: '{locationStr}'")
    return None, None

@app.route('/find-restaurant', methods=['POST'])
def findRestaurant():
    try:
        data = request.json
        budget = data.get('budget')
        timeMinutes = data.get('time')
        transitMode = data.get('transit')
        cuisine = data.get('cuisine')
        dietaryRestriction = data.get('dietary', 'none')
        locationStr = data.get('location')
        getAll = data.get('get_all', False)
        
        currentPreferences = {
            'budget': budget,
            'time': timeMinutes,
            'transit': transitMode,
            'cuisine': cuisine,
            'dietary': dietaryRestriction,
            'location': locationStr
        }
        
        lat, lon = None, None
        
        print(f"Location string received: '{locationStr}'")
        print(f"Stored userLocation: {userLocation}")
        
        if locationStr:
            lat, lon = parseLocationString(locationStr)
            if lat and lon:
                print(f"Successfully parsed location from string: lat={lat}, lon={lon}")
        
        if (not lat or not lon) and userLocation['lat'] and userLocation['lon']:
            lat, lon = userLocation['lat'], userLocation['lon']
            print(f"Using stored user location: lat={lat}, lon={lon}")
        
        if not lat or not lon:
            lat = data.get('latitude')
            lon = data.get('longitude')
            if lat and lon:
                lat, lon = float(lat), float(lon)
                print(f"Using direct lat/lon from request: lat={lat}, lon={lon}")
        
        if not lat or not lon:
            lat, lon = 37.7749, -122.4194
            print("Warning: Using default location (San Francisco)")
        
        print(f"Final coordinates for search: Lat {lat}, Lon {lon}")
        print(f"Filters: Budget={budget}, Time={timeMinutes}min, Transit={transitMode}, Cuisine={cuisine}")
        
        radiusMap = {
            'walking': 5000,
            'biking': 10000,
            'driving': 30000,
            'public_transport': 15000
        }
        radius = radiusMap.get(transitMode.lower() if transitMode else 'driving', 15000)
        
        restaurants = nearbyRestaurants(lat, lon, radius=radius)
        
        if not restaurants:
            return jsonify({
                'status': 'error',
                'message': 'No restaurants found in your area. Try expanding your search radius.'
            })
        
        filteredRestaurants = restaurants
        if timeMinutes and transitMode:
            try:
                timeInt = int(timeMinutes)
                filteredRestaurants = filterByTime(restaurants, lat, lon, timeInt, mode=transitMode)
                oneWayTime = timeInt / 2
                print(f"Filtered to {len(filteredRestaurants)} restaurants within {oneWayTime} minutes one-way ({timeInt} min total round trip) via {transitMode}")
            except Exception as e:
                print(f"Error filtering by time: {e}")
                filteredRestaurants = restaurants
        
        if cuisine and cuisine.lower() != 'any':
            cuisineFiltered = []
            for restaurant in filteredRestaurants:
                restaurantCuisine = restaurant.get('cuisine', '').lower()
                if cuisine.lower() in restaurantCuisine or restaurantCuisine == '':
                    cuisineFiltered.append(restaurant)
            
            if cuisineFiltered:
                filteredRestaurants = cuisineFiltered
        
        if budget:
            budgetFiltered = []
            for restaurant in filteredRestaurants:
                priceRange = restaurant.get('price_range', '')
                if not priceRange or priceRange == 'N/A' or budget in str(priceRange):
                    budgetFiltered.append(restaurant)
            
            if budgetFiltered:
                filteredRestaurants = budgetFiltered
        
        if dietaryRestriction and dietaryRestriction != 'none':
            print(f"Filtering by dietary restriction: {dietaryRestriction}")
            dietaryFiltered = []
            restaurantsWithTags = 0
            
            for restaurant in filteredRestaurants:
                tagsLower = restaurant.get('dietary_tags', '')
                dietVegan = restaurant.get('diet_vegan', '')
                dietVegetarian = restaurant.get('diet_vegetarian', '')
                dietHalal = restaurant.get('diet_halal', '')
                dietKosher = restaurant.get('diet_kosher', '')
                dietGlutenFree = restaurant.get('diet_gluten_free', '')
                dietNutFree = restaurant.get('diet_nut_free', '')
                dietDairyFree = restaurant.get('diet_dairy_free', '')
                
                hasAnyTag = any([dietVegan, dietVegetarian, dietHalal, dietKosher, 
                                  dietGlutenFree, dietNutFree, dietDairyFree, tagsLower])
                if hasAnyTag:
                    restaurantsWithTags += 1
                
                match = False
                restaurantNameLower = restaurant.get('name', '').lower()
                
                if dietaryRestriction == 'vegan':
                    match = (dietVegan == 'yes' or 'vegan' in tagsLower or 
                            'vegan' in restaurantNameLower or
                            (dietVegetarian == 'yes' and 'vegan' in tagsLower))
                elif dietaryRestriction == 'vegetarian':
                    match = (dietVegetarian == 'yes' or 'vegetarian' in tagsLower or 
                            'vegetarian' in restaurantNameLower or
                            dietVegan == 'yes' or 'vegan' in tagsLower or
                            'vegan' in restaurantNameLower)
                elif dietaryRestriction == 'halal':
                    match = (dietHalal == 'yes' or 'halal' in tagsLower or 
                            'halal' in restaurantNameLower)
                elif dietaryRestriction == 'kosher':
                    match = (dietKosher == 'yes' or 'kosher' in tagsLower or 
                            'kosher' in restaurantNameLower)
                elif dietaryRestriction == 'gluten_free':
                    match = (dietGlutenFree == 'yes' or 
                            'gluten-free' in tagsLower or 'gluten free' in tagsLower or
                            'gluten-free' in restaurantNameLower or 'gluten free' in restaurantNameLower)
                elif dietaryRestriction == 'nut_free':
                    match = (dietNutFree == 'yes' or 
                            'nut-free' in tagsLower or 'nut free' in tagsLower or
                            'nut-free' in restaurantNameLower or 'nut free' in restaurantNameLower)
                elif dietaryRestriction == 'dairy_free':
                    match = (dietDairyFree == 'yes' or 
                            'dairy-free' in tagsLower or 'dairy free' in tagsLower or
                            'dairy-free' in restaurantNameLower or 'dairy free' in restaurantNameLower)
                elif dietaryRestriction == 'no_beef':
                    match = ('beef' not in restaurantNameLower and 
                            'beef' not in tagsLower and
                            'steak' not in restaurantNameLower)
                
                if match:
                    dietaryFiltered.append(restaurant)
            
            print(f"Found {restaurantsWithTags} restaurants with dietary tags out of {len(filteredRestaurants)} total")
            print(f"After dietary filtering: {len(dietaryFiltered)} restaurants match '{dietaryRestriction}'")
            
            if dietaryFiltered:
                filteredRestaurants = dietaryFiltered
            else:
                print(f"Warning: No restaurants found matching dietary restriction '{dietaryRestriction}'. Using all restaurants.")
                print("Note: Most restaurants don't have dietary tags in OpenStreetMap data.")
        
        if not filteredRestaurants:
            filteredRestaurants = restaurants
        
        # Filter out the restaurants based on requirements
        excludeNames = data.get('exclude_restaurants', [])
        if excludeNames and not getAll:
            filteredRestaurants = [r for r in filteredRestaurants 
                                   if r.get('name', '') not in excludeNames]
            if not filteredRestaurants:
                filteredRestaurants = restaurants
                excludeNames = []
        
        if getAll:
            print(f"Returning ALL restaurants: {len(filteredRestaurants)} total")
            formattedRestaurants = []
            seenNames = set()
            
            for restaurant in filteredRestaurants:
                restaurantName = restaurant.get('name', 'Unknown Restaurant')
                
                if restaurantName in seenNames:
                    continue
                seenNames.add(restaurantName)
                
                addressParts = [restaurant.get('address', ''), restaurant.get('city', '')]
                fullAddress = ', '.join([p for p in addressParts if p])
                
                formattedRestaurants.append({
                    'name': restaurantName,
                    'cuisine': restaurant.get('cuisine', 'N/A'),
                    'address': fullAddress if fullAddress else 'Address not available',
                    'city': restaurant.get('city', 'N/A'),
                    'price_range': restaurant.get('price_range', budget) if restaurant.get('price_range') != 'N/A' else budget,
                    'travel_time': f"{restaurant.get('eta_minutes', 'N/A')} min" if 'eta_minutes' in restaurant else 'N/A',
                    'coordinates': {
                        'lat': restaurant.get('lat'),
                        'lon': restaurant.get('lon')
                    }
                })
            
            print(f"Formatted {len(formattedRestaurants)} unique restaurants for 'View All'")
            
            return jsonify({
                'status': 'success',
                'all_restaurants': formattedRestaurants,
                'total_count': len(formattedRestaurants)
            })
        
        # Randomly pick a restaurant from the filtered restaurants
        selectedRestaurant = random.choice(filteredRestaurants)
        
        otherOptions = [r for r in filteredRestaurants if r.get('name') != selectedRestaurant.get('name')]
        
        allOptions = [selectedRestaurant] + otherOptions
        formattedOptions = []
        for restaurant in allOptions:
            addressParts = [restaurant.get('address', ''), restaurant.get('city', '')]
            fullAddress = ', '.join([p for p in addressParts if p])
            
            formattedOptions.append({
                'name': restaurant.get('name', 'Unknown Restaurant'),
                'cuisine': restaurant.get('cuisine', 'N/A'),
                'address': fullAddress if fullAddress else 'Address not available',
                'city': restaurant.get('city', 'N/A'),
                'price_range': restaurant.get('price_range', budget) if restaurant.get('price_range') != 'N/A' else budget,
                'travel_time': f"{restaurant.get('eta_minutes', 'N/A')} min" if 'eta_minutes' in restaurant else 'N/A',
                'coordinates': {
                    'lat': restaurant.get('lat'),
                    'lon': restaurant.get('lon')
                }
            })
        
        return jsonify({
            'status': 'success',
            'restaurant': formattedOptions[0],
            'all_restaurants': formattedOptions,
            'preferences': {
                'budget': budget,
                'time': timeMinutes,
                'transit': transitMode,
                'cuisine': cuisine
            }
        })
        
    except Exception as e:
        import traceback
        print(f"Error in findRestaurant: {e}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Error finding restaurant: {str(e)}'
        }), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
