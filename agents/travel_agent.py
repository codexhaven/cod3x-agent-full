"""
Travel Agent - Trip planning and travel recommendations
"""

import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime

class TravelAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.search_tool = cod3x.tools.get('serpapi')
    
    async def initialize(self):
        self.logger.info("Travel Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process travel-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['plan trip', 'travel to', 'visit', 'vacation']):
                return await self._plan_trip(request, user_id)
            elif any(kw in text_lower for kw in ['flight', 'fly to']):
                return await self._search_flights(request, user_id)
            elif any(kw in text_lower for kw in ['hotel', 'accommodation', 'stay']):
                return await self._search_hotels(request, user_id)
            elif any(kw in text_lower for kw in ['itinerary', 'trip schedule']):
                return await self._generate_itinerary(request, user_id)
            elif any(kw in text_lower for kw in ['travel tip', 'what to do', 'attractions']):
                return await self._get_recommendations(request, user_id)
            else:
                return await self._get_travel_assistance(user_id)
        except Exception as e:
            self.logger.error(f"Travel agent error: {e}")
            return "I had trouble with travel planning. Please try again."
    
    async def _plan_trip(self, request: str, user_id: str) -> str:
        """Plan a trip"""
        trip_details = await self._extract_trip_details(request)
        
        if not trip_details.get('destination'):
            return "🌍 Where would you like to travel to? Please specify a destination."
        
        # Store trip in memory
        await self.cod3x.memory['sqlite'].store_trip(user_id, trip_details)
        
        response = f"🌍 **Planning trip to {trip_details['destination']}**\n\n"
        
        # Get travel info if Gemini is available
        if self.model:
            prompt = f"""Create a travel brief for:
            Destination: {trip_details['destination']}
            Dates: {trip_details.get('start_date', 'flexible')} to {trip_details.get('end_date', 'flexible')}
            Budget: {trip_details.get('budget', 'moderate')}
            
            Include:
            1. Best time to visit
            2. Must-see attractions
            3. Estimated costs
            4. Travel tips"""
            
            try:
                response_text = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                response += response_text.text
            except:
                response += self._get_fallback_travel_info(trip_details['destination'])
        
        return response
    
    async def _extract_trip_details(self, request: str) -> Dict:
        """Extract trip details from request"""
        if self.model:
            prompt = f"""Extract trip details from: {request}
            Return JSON: {{"destination": "city/country", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "budget": "budget/luxury/moderate", "travelers": number}}"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return json.loads(response.text)
            except:
                pass
        
        # Fallback extraction
        trip = {
            "destination": "",
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now()).strftime("%Y-%m-%d"),
            "budget": "moderate",
            "travelers": 1
        }
        
        text = request.lower()
        
        # Extract destination
        for prefix in ['travel to', 'visit', 'trip to', 'vacation in']:
            if prefix in text:
                parts = text.split(prefix, 1)
                if len(parts) > 1:
                    trip['destination'] = parts[1].strip().title().split(',')[0].split('.')[0]
                break
        
        return trip
    
    async def _search_flights(self, request: str, user_id: str) -> str:
        """Search for flights"""
        if self.search_tool:
            try:
                # Extract flight search params
                flight_params = await self._extract_flight_params(request)
                
                if flight_params.get('destination'):
                    results = await self.search_tool.search(
                        f"flights to {flight_params['destination']} from {flight_params.get('origin', 'my location')} {flight_params.get('date', '')}"
                    )
                    return f"✈️ **Flight search results for {flight_params['destination']}:**\n\n{results[:500]}"
            except:
                pass
        
        return "✈️ Flight search requires API configuration. Please specify dates for better results."
    
    async def _extract_flight_params(self, request: str) -> Dict:
        """Extract flight search parameters"""
        params = {
            "origin": "",
            "destination": "",
            "date": ""
        }
        
        text = request.lower()
        
        if 'to ' in text:
            parts = text.split('to ', 1)
            if len(parts) > 1:
                params['destination'] = parts[1].split()[0].strip().title()
        
        if 'from ' in text:
            parts = text.split('from ', 1)
            if len(parts) > 1:
                params['origin'] = parts[1].split()[0].strip().title()
        
        return params
    
    async def _search_hotels(self, request: str, user_id: str) -> str:
        """Search for hotels"""
        if self.search_tool:
            try:
                destination = ""
                text = request.lower()
                for prefix in ['hotel in', 'stay in', 'accommodation in']:
                    if prefix in text:
                        destination = text.split(prefix, 1)[1].strip().title()
                        break
                
                if destination:
                    results = await self.search_tool.search(f"hotels in {destination}")
                    return f"🏨 **Hotels in {destination}:**\n\n{results[:500]}"
            except:
                pass
        
        return "🏨 Hotel search available. Specify your destination and preferences."
    
    async def _generate_itinerary(self, request: str, user_id: str) -> str:
        """Generate travel itinerary"""
        trips = await self.cod3x.memory['sqlite'].get_trips(user_id, limit=1)
        
        if not trips:
            return "🌍 No trips planned. Say 'plan trip to [destination]' first!"
        
        trip = trips[0]
        
        if self.model:
            prompt = f"""Create a detailed day-by-day itinerary for a trip to {trip.get('destination')}:
            Duration: {trip.get('duration', '3-5')} days
            Budget: {trip.get('budget', 'moderate')}
            
            Include morning, afternoon, and evening activities with estimated costs."""
            
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )
            return f"📋 **Itinerary for {trip.get('destination')}:**\n\n{response.text}"
        
        return f"📋 Itinerary generation for {trip.get('destination')} requires Gemini API."
    
    async def _get_recommendations(self, request: str, user_id: str) -> str:
        """Get travel recommendations"""
        destination = ""
        text = request.lower()
        for prefix in ['what to do in', 'attractions in', 'things to do in']:
            if prefix in text:
                destination = text.split(prefix, 1)[1].strip().title()
                break
        
        if destination and self.model:
            prompt = f"List top attractions and activities in {destination} with brief descriptions."
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )
            return f"🎯 **Top Attractions in {destination}:**\n\n{response.text}"
        
        return "🎯 Tell me your destination for personalized recommendations!"
    
    def _get_fallback_travel_info(self, destination: str) -> str:
        """Fallback travel info without API"""
        popular_destinations = {
            'paris': "• Best time: Spring/Fall\n• Must-see: Eiffel Tower, Louvre\n• Budget: $150-300/day",
            'tokyo': "• Best time: Spring/March-May\n• Must-see: Shibuya, temples\n• Budget: $100-250/day",
            'new york': "• Best time: Fall/September-November\n• Must-see: Central Park, Times Square\n• Budget: $200-400/day"
        }
        
        dest_lower = destination.lower()
        for city, info in popular_destinations.items():
            if city in dest_lower:
                return info
        
        return "• Research your destination online for best results\n• Book flights 2-3 months in advance\n• Check visa requirements"
    
    async def _get_travel_assistance(self, user_id: str) -> str:
        """Get travel assistance overview"""
        trips = await self.cod3x.memory['sqlite'].get_trips(user_id)
        
        response = "🌍 **Travel Assistant**\n\n"
        response += "• 'plan trip to [place]' - Start planning\n"
        response += "• 'flights to [place]' - Find flights\n"
        response += "• 'hotels in [place]' - Find accommodation\n"
        response += "• 'itinerary' - Generate day plan\n"
        
        if trips:
            response += f"\n📋 Active trips: {len(trips)}\n"
            response += f"• {trips[0].get('destination', 'Unknown')}"
        
        return response
    
    async def shutdown(self):
        pass
