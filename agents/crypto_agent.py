from llm_proxy import generate as llm_generate
"""
Crypto Agent - Cryptocurrency prices, analysis, and tracking
"""

import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime

class CryptoAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        from utils.free_ai import get_ai; self.model = get_ai()
        self.search_tool = cod3x.tools.get('serpapi')
    
    async def initialize(self):
        self.logger.info("Crypto Agent initialized")
        # Cache for crypto prices to avoid rate limiting
        self.price_cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process crypto-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['price', 'value', 'worth', 'cost']):
                return await self._get_price(request, user_id)
            elif any(kw in text_lower for kw in ['portfolio', 'my crypto', 'holdings']):
                return await self._manage_portfolio(request, user_id)
            elif any(kw in text_lower for kw in ['market', 'cap', 'volume']):
                return await self._market_overview(user_id)
            elif any(kw in text_lower for kw in ['trend', 'chart', 'graph', 'performance']):
                return await self._analyze_trend(request, user_id)
            elif any(kw in text_lower for kw in ['news', 'update']):
                return await self._crypto_news(request, user_id)
            else:
                return await self._crypto_overview(user_id)
        except Exception as e:
            self.logger.error(f"Crypto agent error: {e}")
            return "I had trouble with crypto data. Please try again."
    
    async def _get_price(self, request: str, user_id: str) -> str:
        """Get cryptocurrency price"""
        coin = await self._extract_coin(request)
        
        if not coin:
            coin = 'bitcoin'
        
        # Check cache
        cache_key = f"{coin}_price"
        if cache_key in self.price_cache:
            cached = self.price_cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < self.cache_timeout:
                price_data = cached['data']
                return self._format_price_response(coin, price_data)
        
        # Get price from search or Gemini
        price_data = await self._fetch_price(coin)
        
        if price_data:
            # Update cache
            self.price_cache[cache_key] = {
                'data': price_data,
                'timestamp': datetime.now()
            }
            
            # Store in memory
            await self.cod3x.memory['sqlite'].store_crypto_query(user_id, {
                'coin': coin,
                'price': price_data.get('price'),
                'timestamp': datetime.now().isoformat()
            })
            
            return self._format_price_response(coin, price_data)
        
        return f"💎 Unable to get {coin.title()} price. Market data temporarily unavailable."
    
    async def _extract_coin(self, request: str) -> str:
        """Extract coin name from request"""
        text = request.lower()
        
        coins = {
            'bitcoin': ['bitcoin', 'btc'],
            'ethereum': ['ethereum', 'eth'],
            'dogecoin': ['dogecoin', 'doge'],
            'cardano': ['cardano', 'ada'],
            'solana': ['solana', 'sol'],
            'ripple': ['ripple', 'xrp'],
            'polkadot': ['polkadot', 'dot'],
            'litecoin': ['litecoin', 'ltc']
        }
        
        for coin_name, keywords in coins.items():
            if any(kw in text for kw in keywords):
                return coin_name
        
        # Try to find any coin mentioned
        for word in text.split():
            if word in coins:
                return word
        
        return 'bitcoin'
    
    async def _fetch_price(self, coin: str) -> Dict:
        """Fetch cryptocurrency price"""
        price_data = {}
        
        # Try web search
        if self.search_tool:
            try:
                results = await self.search_tool.search(f"{coin} price USD today")
                # Parse price from search results (simplified)
                import re
                price_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', results)
                if price_match:
                    price_data['price'] = float(price_match.group(1).replace(',', ''))
            except:
                pass
        
        # Use Gemini as fallback with simulated data
        if self.model:
            try:
                prompt = f"What is the current approximate price of {coin} in USD? Return just the price and 24h change."
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                # Parse response for price
                import re
                price_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', response)
                if price_match:
                    price_data['price'] = float(price_match.group(1).replace(',', ''))
                
                change_match = re.search(r'([+-]?\d+\.?\d*)%', response)
                if change_match:
                    price_data['change_24h'] = float(change_match.group(1))
            except:
                pass
        
        return price_data
    
    def _format_price_response(self, coin: str, data: Dict) -> str:
        """Format price response"""
        response = f"💎 **{coin.title()} Price**\n\n"
        
        if data.get('price'):
            response += f"💰 Price: ${data['price']:,.2f} USD\n"
        
        if data.get('change_24h'):
            emoji = "📈" if data['change_24h'] > 0 else "📉"
            response += f"{emoji} 24h Change: {data['change_24h']:+.2f}%\n"
        
        response += f"\n🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"
        
        return response
    
    async def _manage_portfolio(self, request: str, user_id: str) -> str:
        """Manage crypto portfolio"""
        text_lower = request.lower()
        
        if any(kw in text_lower for kw in ['add', 'buy', 'bought']):
            # Add to portfolio
            coin = await self._extract_coin(request)
            amount = 1.0
            
            import re
            amount_match = re.search(r'(\d+\.?\d*)', text_lower)
            if amount_match:
                amount = float(amount_match.group(1))
            
            await self.cod3x.memory['sqlite'].add_to_portfolio(user_id, {
                'coin': coin,
                'amount': amount,
                'date': datetime.now().isoformat()
            })
            
            return f"💎 Added {amount} {coin.upper()} to your portfolio"
        
        elif any(kw in text_lower for kw in ['show', 'list', 'view']):
            # Show portfolio
            portfolio = await self.cod3x.memory['sqlite'].get_portfolio(user_id)
            
            if not portfolio:
                return "💎 Your portfolio is empty. Say 'buy [amount] [coin]' to start tracking!"
            
            response = "💎 **Your Crypto Portfolio**\n\n"
            total_value = 0
            
            for holding in portfolio:
                coin = holding.get('coin', 'unknown')
                amount = holding.get('amount', 0)
                
                # Get current price
                price_data = await self._fetch_price(coin)
                price = price_data.get('price', 0)
                value = amount * price
                total_value += value
                
                response += f"• {coin.upper()}: {amount} @ ${price:,.2f} = ${value:,.2f}\n"
            
            response += f"\n💰 Total Value: ${total_value:,.2f}"
            
            return response
        
        return "💎 Use 'buy [amount] [coin]' to track or 'show portfolio' to view"
    
    async def _market_overview(self, user_id: str) -> str:
        """Get market overview"""
        if self.model:
            try:
                prompt = "Provide a brief crypto market overview: total market cap, BTC dominance, top movers, and market sentiment."
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                return f"📊 **Crypto Market Overview**\n\n{response}"
            except:
                pass
        
        # Fallback top coins
        top_coins = ['bitcoin', 'ethereum', 'binance coin', 'cardano', 'solana']
        response = "📊 **Market Overview**\n\n"
        
        for coin in top_coins:
            price_data = await self._fetch_price(coin)
            if price_data.get('price'):
                response += f"• {coin.title()}: ${price_data['price']:,.2f}\n"
        
        return response
    
    async def _analyze_trend(self, request: str, user_id: str) -> str:
        """Analyze crypto trends"""
        coin = await self._extract_coin(request)
        
        if self.model:
            try:
                prompt = f"Analyze recent price trends and provide a brief outlook for {coin}. Include support/resistance levels if possible."
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                return f"📈 **{coin.title()} Analysis**\n\n{response}"
            except:
                pass
        
        return f"📈 Trend analysis for {coin.title()}. I'll analyze price patterns and market sentiment."
    
    async def _crypto_news(self, request: str, user_id: str) -> str:
        """Get crypto news"""
        if self.model:
            try:
                prompt = "What are the top 3 crypto news stories right now? Provide brief summaries."
                response = await asyncio.to_thread(
                    self.model._call, prompt
                )
                return f"📰 **Crypto News**\n\n{response}"
            except:
                pass
        
        return "📰 Crypto news updates (check CoinDesk or CoinTelegraph for latest)"
    
    async def _crypto_overview(self, user_id: str) -> str:
        """Crypto assistant overview"""
        return "💎 **Crypto Assistant**\n\n• 'price of [coin]' - Get prices\n• 'buy [amount] [coin]' - Track holdings\n• 'market overview' - Market stats\n• 'trend [coin]' - Analysis\n• 'crypto news' - Latest updates"
    
    async def shutdown(self):
        pass
