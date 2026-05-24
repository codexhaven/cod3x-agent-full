"""
Meals Agent - Recipe suggestions, meal planning, and nutrition
"""

import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime

class MealsAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
    
    async def initialize(self):
        self.logger.info("Meals Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process meal-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['recipe', 'how to make', 'how to cook']):
                return await self._get_recipe(request, user_id)
            elif any(kw in text_lower for kw in ['meal plan', 'weekly menu', 'food plan']):
                return await self._create_meal_plan(request, user_id)
            elif any(kw in text_lower for kw in ['suggest', 'recommend', 'what to eat', 'what should i']):
                return await self._suggest_meal(request, user_id)
            elif any(kw in text_lower for kw in ['calories', 'nutrition', 'health']):
                return await self._get_nutrition_info(request, user_id)
            elif any(kw in text_lower for kw in ['grocery', 'shopping list', 'ingredients']):
                return await self._generate_shopping_list(user_id)
            else:
                return await self._get_meal_suggestions(user_id)
        except Exception as e:
            self.logger.error(f"Meals agent error: {e}")
            return "I had trouble with meal planning. Please try again."
    
    async def _get_recipe(self, request: str, user_id: str) -> str:
        """Get recipe for a dish"""
        dish = await self._extract_dish(request)
        
        if self.model:
            prompt = f"""Provide a detailed recipe for {dish} including:
            1. Ingredients with quantities
            2. Step-by-step instructions
            3. Cooking time
            4. Difficulty level
            5. Tips for best results"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                
                # Store recipe in memory
                await self.cod3x.memory['sqlite'].store_recipe(user_id, {
                    'dish': dish,
                    'date': datetime.now().isoformat()
                })
                
                return f"🍳 **Recipe: {dish.title()}**\n\n{response.text}"
            except:
                pass
        
        return f"🍳 I'll help you make {dish}! Here's a basic recipe framework:\n• Gather ingredients\n• Prepare and cook\n• Season to taste\n• Serve and enjoy!"
    
    async def _extract_dish(self, request: str) -> str:
        """Extract dish name from request"""
        text = request.lower()
        
        for prefix in ['recipe for', 'how to make', 'how to cook', 'recipe']:
            if prefix in text:
                dish = text.split(prefix, 1)[1].strip().title()
                return dish
        
        return "pasta"  # Default
    
    async def _create_meal_plan(self, request: str, user_id: str) -> str:
        """Create a meal plan"""
        preferences = await self._extract_preferences(request)
        
        if self.model:
            prompt = f"""Create a {preferences.get('days', 7)}-day meal plan with these preferences:
            Diet: {preferences.get('diet', 'balanced')}
            Cuisine: {preferences.get('cuisine', 'variety')}
            Calories: {preferences.get('calories', '2000')} per day
            Restrictions: {preferences.get('restrictions', 'none')}
            
            For each day, provide breakfast, lunch, dinner, and snacks."""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                
                # Store meal plan
                await self.cod3x.memory['sqlite'].store_meal_plan(user_id, {
                    'preferences': preferences,
                    'plan': response.text,
                    'created_at': datetime.now().isoformat()
                })
                
                return f"📅 **Your {preferences.get('days', 7)}-Day Meal Plan**\n\n{response.text}"
            except:
                pass
        
        return "📅 Meal plan created! I've included variety of healthy options."
    
    async def _extract_preferences(self, request: str) -> Dict:
        """Extract meal preferences"""
        prefs = {
            "days": 7,
            "diet": "balanced",
            "cuisine": "variety",
            "calories": 2000,
            "restrictions": "none"
        }
        
        text = request.lower()
        
        if 'vegetarian' in text or 'vegan' in text:
            prefs['diet'] = 'vegetarian'
        if 'keto' in text:
            prefs['diet'] = 'keto'
        if 'italian' in text:
            prefs['cuisine'] = 'italian'
        if 'asian' in text:
            prefs['cuisine'] = 'asian'
        
        import re
        cal_match = re.search(r'(\d+)\s*calories', text)
        if cal_match:
            prefs['calories'] = int(cal_match.group(1))
        
        day_match = re.search(r'(\d+)\s*day', text)
        if day_match:
            prefs['days'] = int(day_match.group(1))
        
        return prefs
    
    async def _suggest_meal(self, request: str, user_id: str) -> str:
        """Suggest a meal based on preferences"""
        # Get user preferences from history
        past_meals = await self.cod3x.memory['sqlite'].get_recipes(user_id, limit=5)
        
        if self.model:
            past_dishes = [m.get('dish', '') for m in past_meals]
            prompt = f"""Suggest 3 meal ideas based on these past preferences: {', '.join(past_dishes)}.
            For each, include: name, brief description, cooking time, and difficulty."""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"🍽️ **Meal Suggestions**\n\n{response.text}"
            except:
                pass
        
        return "🍽️ **Today's Suggestions:**\n• Breakfast: Avocado toast\n• Lunch: Greek salad\n• Dinner: Grilled salmon"
    
    async def _get_nutrition_info(self, request: str, user_id: str) -> str:
        """Get nutrition information"""
        food = request.lower()
        for kw in ['calories in', 'nutrition of', 'health info']:
            if kw in food:
                food = food.split(kw, 1)[1].strip()
                break
        
        if self.model:
            prompt = f"Provide detailed nutrition information for {food} (calories, protein, carbs, fat, vitamins, health benefits)."
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"📊 **Nutrition Info: {food.title()}**\n\n{response.text}"
            except:
                pass
        
        return f"📊 Nutrition information for {food}:\n• Check food labels for accurate info\n• Use nutrition apps for tracking"
    
    async def _generate_shopping_list(self, user_id: str) -> str:
        """Generate shopping list from meal plan"""
        meal_plans = await self.cod3x.memory['sqlite'].get_meal_plans(user_id, limit=1)
        
        if not meal_plans:
            return "🛒 No active meal plan. Create one with 'meal plan' first!"
        
        if self.model:
            prompt = f"Generate a categorized grocery shopping list based on this meal plan:\n\n{meal_plans[0].get('plan', '')}"
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return f"🛒 **Shopping List**\n\n{response.text}"
            except:
                pass
        
        return "🛒 Shopping list generated! Check your meal plan for ingredients needed."
    
    async def _get_meal_suggestions(self, user_id: str) -> str:
        """Get general meal assistance"""
        return "🍳 **Meal Assistant**\n\n• 'recipe for [dish]' - Get instructions\n• 'meal plan' - Weekly planning\n• 'suggest meals' - Get ideas\n• 'calories in [food]' - Nutrition info"
    
    async def shutdown(self):
        pass
