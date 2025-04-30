"""Wrapper to Google Maps Places API."""

import os
from typing import Dict, List, Any, Optional

from google.adk.tools import ToolContext
import requests


class PlacesService:
    """Wrapper to Placees API."""

    def _check_key(self):
        if (
            not hasattr(self, "places_api_key") or not self.places_api_key
        ):  # Either it doesn't exist or is None.
            # https://developers.google.com/maps/documentation/places/web-service/get-api-key
            self.places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    def find_place_from_text(self, query: str) -> Dict[str, Any]:
        """
        Find a place using a text query via Google Places API.

        Args:
            query: The search query (e.g., "Eiffel Tower Paris").

        Returns:
            A dictionary with place_id, place_name, place_address, photos (list), map_url, lat, lng.
            If no place is found, returns {'error': ...}
        """
        self._check_key()
        places_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {
            "input": query,
            "inputtype": "textquery",
            "fields": "place_id,formatted_address,name,photos,geometry",
            "key": self.places_api_key,
        }

        try:
            response = requests.get(places_url, params=params)
            response.raise_for_status()
            place_data = response.json()

            if not place_data.get("candidates"):
                return {"error": "No places found."}

            # Extract data for the first candidate
            place_details = place_data["candidates"][0]
            place_id = place_details["place_id"]
            place_name = place_details["name"]
            place_address = place_details["formatted_address"]
            photos = self.get_photo_urls(place_details.get("photos", []), maxwidth=400)
            map_url = self.get_map_url(place_id)
            location = place_details["geometry"]["location"]
            lat = str(location["lat"])
            lng = str(location["lng"])

            return {
                "place_id": place_id,
                "place_name": place_name,
                "place_address": place_address,
                "photos": photos,
                "map_url": map_url,
                "lat": lat,
                "lng": lng,
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"Error fetching place data: {e}"}

    def get_photo_urls(self, photos: List[Dict[str, Any]], maxwidth: int = 400) -> List[str]:
        """Helper to build photo URLs from Google Places API photo references."""
        if not photos:
            return []
        base_url = "https://maps.googleapis.com/maps/api/place/photo"
        return [
            f"{base_url}?maxwidth={maxwidth}&photoreference={photo['photo_reference']}&key={self.places_api_key}"
            for photo in photos
        ]

    def get_map_url(self, place_id: str) -> str:
        """Helper to build a Google Maps URL for a place."""
        return f"https://www.google.com/maps/place/?q=place_id:{place_id}"


# Google Places API
places_service = PlacesService()


def map_tool(key: str, tool_context: ToolContext):
    """
    This is going to inspect the pois stored under the specified key in the state.
    One by one it will retrieve the accurate Lat/Lon from the Map API, if the Map API is available for use.

    Args:
        key: The key under which the POIs are stored.
        tool_context: The ADK tool context.
        
    Returns:
        The updated state with the full JSON object under the key.
    """
    if key not in tool_context.state:
        tool_context.state[key] = {}

    # The pydantic object types.POISuggestions
    if "places" not in tool_context.state[key]:
        tool_context.state[key]["places"] = []

    pois = tool_context.state[key]["places"]
    for poi in pois:  # The pydantic object types.POI
        location = poi["place_name"] + ", " + poi["address"]
        result = places_service.find_place_from_text(location)
        # Fill the place holders with verified information.
        poi["place_id"] = result["place_id"] if "place_id" in result else None
        poi["map_url"] = result["map_url"] if "map_url" in result else None
        if "lat" in result and "lng" in result:
            poi["lat"] = result["lat"]
            poi["long"] = result["lng"]

    return {"places": pois}  # Return the updated pois


# """Wrapper to Google Maps Places API."""

# import os
# from typing import Dict, List, Any, Optional

# from google.adk.tools import ToolContext
# import requests


# class PlacesService:
#     """Wrapper to Placees API."""

#     def _check_key(self):
#         if (
#             not hasattr(self, "places_api_key") or not self.places_api_key
#         ):  # Either it doesn't exist or is None.
#             # https://developers.google.com/maps/documentation/places/web-service/get-api-key
#             self.places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")

#     def find_place_from_text(self, query: str) -> Dict[str, Any]:
#         """
#         Find a place using a text query via Google Places API.

#         Args:
#             query: The search query (e.g., "Eiffel Tower Paris").

#         Returns:
#             A dictionary with place_id, place_name, place_address, photos (list), map_url, lat, lng.
#             If no place is found, returns {'error': ...}
#         """
#         self._check_key()
#         places_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
#         params = {
#             "input": query,
#             "inputtype": "textquery",
#             "fields": "place_id,formatted_address,name,photos,geometry",
#             "key": self.places_api_key,
#         }

#         try:
#             response = requests.get(places_url, params=params)
#             response.raise_for_status()
#             place_data = response.json()

#             if not place_data.get("candidates"):
#                 return {"error": "No places found."}

#             # Extract data for the first candidate
#             place_details = place_data["candidates"][0]
#             place_id = place_details["place_id"]
#             place_name = place_details["name"]
#             place_address = place_details["formatted_address"]
#             location = place_details["geometry"]["location"]
#             lat = str(location["lat"])
#             lng = str(location["lng"])

#             return {
#                 "place_id": place_id,
#                 "place_name": place_name,
#                 "place_address": place_address,
#                 "lat": lat,
#                 "lng": lng,
#             }

#         except requests.exceptions.RequestException as e:
#             return {"error": f"Error fetching place data: {e}"}

# # Google Places API
# places_service = PlacesService()