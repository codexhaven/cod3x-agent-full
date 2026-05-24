"""
Helper Utilities
"""

import asyncio
import json
import os
import re
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

class Helpers:
    """General helper functions"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:251] + ext
        return filename
    
    @staticmethod
    def generate_id(prefix: str = '') -> str:
        """Generate a unique ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        random_bytes = os.urandom(4).hex()
        id_str = f"{timestamp}{random_bytes}"[:16]
        return f"{prefix}_{id_str}" if prefix else id_str
    
    @staticmethod
    def parse_date(date_string: str) -> Optional[datetime]:
        """Parse date string in various formats"""
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # Try natural language
        date_string_lower = date_string.lower()
        now = datetime.now()
        
        if date_string_lower == 'today':
            return now
        elif date_string_lower == 'tomorrow':
            return now + timedelta(days=1)
        elif date_string_lower == 'yesterday':
            return now - timedelta(days=1)
        elif 'next week' in date_string_lower:
            return now + timedelta(days=7)
        elif 'next month' in date_string_lower:
            return now + timedelta(days=30)
        
        return None
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m" if minutes else f"{hours}h"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h" if hours else f"{days}d"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 200, suffix: str = '...') -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_entities(text: str) -> Dict[str, List[str]]:
        """Extract basic entities from text"""
        entities = {
            'emails': [],
            'urls': [],
            'phones': [],
            'hashtags': [],
            'mentions': []
        }
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Extract URLs
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*'
        entities['urls'] = re.findall(url_pattern, text)
        
        # Extract phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        entities['phones'] = re.findall(phone_pattern, text)
        
        # Extract hashtags
        hashtag_pattern = r'#\w+'
        entities['hashtags'] = re.findall(hashtag_pattern, text)
        
        # Extract mentions
        mention_pattern = r'@\w+'
        entities['mentions'] = re.findall(mention_pattern, text)
        
        return entities
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate simple text similarity (Jaccard)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 4000) -> List[str]:
        """Split text into chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    @staticmethod
    def safe_json_loads(data: str, default: Any = None) -> Any:
        """Safely load JSON with fallback"""
        try:
            return json.loads(data)
        except:
            return default if default is not None else {}
    
    @staticmethod
    def safe_json_dumps(data: Any, indent: int = 2) -> str:
        """Safely dump JSON with fallback"""
        try:
            return json.dumps(data, indent=indent, default=str)
        except:
            return str(data)
    
    @staticmethod
    def retry_async(func, max_retries: int = 3, delay: float = 1.0):
        """Retry async function with exponential backoff"""
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
            return None
        return wrapper
    
    @staticmethod
    def cache_result(func, ttl_seconds: int = 300):
        """Cache async function results"""
        cache = {}
        
        async def wrapper(*args, **kwargs):
            key = hashlib.md5(
                f"{func.__name__}{args}{kwargs}".encode()
            ).hexdigest()
            
            if key in cache:
                result, timestamp = cache[key]
                if (datetime.now() - timestamp).seconds < ttl_seconds:
                    return result
            
            result = await func(*args, **kwargs)
            cache[key] = (result, datetime.now())
            return result
        
        return wrapper
    
    @staticmethod
    def format_table(data: List[Dict], columns: List[str]) -> str:
        """Format data as a text table"""
        if not data:
            return "No data"
        
        # Calculate column widths
        col_widths = {col: len(col) for col in columns}
        for row in data:
            for col in columns:
                value = str(row.get(col, ''))
                col_widths[col] = max(col_widths[col], len(value))
        
        # Build table
        lines = []
        
        # Header
        header = ' | '.join(col.ljust(col_widths[col]) for col in columns)
        lines.append(header)
        lines.append('-' * len(header))
        
        # Data rows
        for row in data:
            line = ' | '.join(
                str(row.get(col, '')).ljust(col_widths[col]) 
                for col in columns
            )
            lines.append(line)
        
        return '\n'.join(lines)

# Create singleton instance
helpers = Helpers()
