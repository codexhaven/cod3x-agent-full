"""
SQLite Memory - Persistent structured data storage
"""

import asyncio
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

class SQLiteMemory:
    def __init__(self, config: Dict):
        self.config = config
        self.db_path = config.get('sqlite_path', 'cod3x_memory.db')
        self.connection = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            
            # Create tables
            await self._create_tables()
            
            self.initialized = True
            print(f"SQLite Memory initialized: {self.db_path}")
        except Exception as e:
            print(f"SQLite initialization error: {e}")
            self.initialized = False
    
    async def _create_tables(self):
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                date TEXT,
                time TEXT,
                duration INTEGER,
                description TEXT,
                location TEXT,
                attendees TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Contacts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                company TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                type TEXT DEFAULT 'document',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'other',
                date TEXT,
                payment_method TEXT DEFAULT 'other',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT DEFAULT 'all',
                period TEXT DEFAULT 'monthly',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trips table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                destination TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT,
                budget TEXT,
                travelers INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Recipes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                dish TEXT NOT NULL,
                date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Meal plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preferences TEXT,
                plan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Portfolio table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                coin TEXT NOT NULL,
                amount REAL DEFAULT 0,
                date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crypto queries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                coin TEXT NOT NULL,
                price REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Social posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                platform TEXT,
                content TEXT,
                topic TEXT,
                status TEXT DEFAULT 'draft',
                scheduled_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Content table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                topic TEXT,
                content TEXT,
                type TEXT DEFAULT 'article',
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Image prompts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                prompt TEXT,
                status TEXT DEFAULT 'generated',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Drafts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tweets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                text TEXT,
                status TEXT DEFAULT 'draft',
                thread_position INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
    
    async def _execute(self, query: str, params: tuple = None) -> List:
        """Execute SQL query"""
        def _run():
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.fetchall()
        
        return await asyncio.to_thread(_run)
    
    # Event methods
    async def store_event(self, user_id: str, event: Dict):
        query = '''INSERT INTO events (user_id, title, date, time, duration, description, location, attendees)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
        params = (
            user_id,
            event.get('title', 'Untitled'),
            event.get('date', ''),
            event.get('time', ''),
            event.get('duration', 60),
            event.get('description', ''),
            event.get('location', ''),
            json.dumps(event.get('attendees', []))
        )
        await self._execute(query, params)
    
    async def get_events(self, user_id: str, limit: int = 10) -> List[Dict]:
        query = '''SELECT * FROM events WHERE user_id = ? ORDER BY date, time LIMIT ?'''
        rows = await self._execute(query, (user_id, limit))
        return [dict(row) for row in rows]
    
    async def update_event(self, user_id: str, event: Dict):
        query = '''UPDATE events SET title = ?, date = ?, time = ? WHERE user_id = ? AND title = ?'''
        await self._execute(query, (
            event.get('title'),
            event.get('date'),
            event.get('time'),
            user_id,
            event.get('title')
        ))
    
    async def delete_event(self, user_id: str, title: str):
        await self._execute('DELETE FROM events WHERE user_id = ? AND title = ?', (user_id, title))
    
    # Task methods
    async def store_task(self, user_id: str, task: Dict):
        query = '''INSERT INTO tasks (user_id, title, description, priority, due_date, status)
                   VALUES (?, ?, ?, ?, ?, ?)'''
        params = (
            user_id,
            task.get('title', 'New Task'),
            task.get('description', ''),
            task.get('priority', 'medium'),
            task.get('due_date', ''),
            task.get('status', 'pending')
        )
        await self._execute(query, params)
    
    async def get_tasks(self, user_id: str, status: str = None) -> List[Dict]:
        if status:
            query = 'SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY priority, due_date'
            rows = await self._execute(query, (user_id, status))
        else:
            query = 'SELECT * FROM tasks WHERE user_id = ? ORDER BY priority, due_date'
            rows = await self._execute(query, (user_id,))
        return [dict(row) for row in rows]
    
    async def update_task(self, user_id: str, title: str, status: str):
        await self._execute(
            'UPDATE tasks SET status = ? WHERE user_id = ? AND title = ?',
            (status, user_id, title)
        )
    
    async def delete_task(self, user_id: str, title: str):
        await self._execute('DELETE FROM tasks WHERE user_id = ? AND title = ?', (user_id, title))
    
    # Contact methods
    async def store_contact(self, user_id: str, contact: Dict):
        query = '''INSERT INTO contacts (user_id, name, email, phone, company, notes)
                   VALUES (?, ?, ?, ?, ?, ?)'''
        params = (
            user_id,
            contact.get('name', 'Unknown'),
            contact.get('email', ''),
            contact.get('phone', ''),
            contact.get('company', ''),
            contact.get('notes', '')
        )
        await self._execute(query, params)
    
    async def get_contacts(self, user_id: str) -> List[Dict]:
        rows = await self._execute('SELECT * FROM contacts WHERE user_id = ?', (user_id,))
        return [dict(row) for row in rows]
    
    async def delete_contact(self, user_id: str, name: str):
        await self._execute('DELETE FROM contacts WHERE user_id = ? AND name = ?', (user_id, name))
    
    # Document methods
    async def store_document(self, user_id: str, doc: Dict):
        query = '''INSERT INTO documents (user_id, title, content, type) VALUES (?, ?, ?, ?)'''
        params = (user_id, doc.get('title', 'Untitled'), doc.get('content', ''), doc.get('type', 'document'))
        await self._execute(query, params)
    
    async def get_documents(self, user_id: str, limit: int = 10) -> List[Dict]:
        rows = await self._execute(
            'SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        return [dict(row) for row in rows]
    
    # Expense methods
    async def store_expense(self, user_id: str, expense: Dict):
        query = '''INSERT INTO expenses (user_id, amount, description, category, date, payment_method)
                   VALUES (?, ?, ?, ?, ?, ?)'''
        params = (
            user_id,
            expense.get('amount', 0),
            expense.get('description', ''),
            expense.get('category', 'other'),
            expense.get('date', datetime.now().strftime('%Y-%m-%d')),
            expense.get('payment_method', 'other')
        )
        await self._execute(query, params)
    
    async def get_expenses(self, user_id: str, category: str = None, limit: int = 50) -> List[Dict]:
        if category:
            rows = await self._execute(
                'SELECT * FROM expenses WHERE user_id = ? AND category = ? ORDER BY date DESC LIMIT ?',
                (user_id, category, limit)
            )
        else:
            rows = await self._execute(
                'SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT ?',
                (user_id, limit)
            )
        return [dict(row) for row in rows]
    
    # Budget methods
    async def set_budget(self, user_id: str, budget: Dict):
        query = '''INSERT INTO budgets (user_id, amount, category, period) VALUES (?, ?, ?, ?)'''
        params = (user_id, budget.get('amount', 0), budget.get('category', 'all'), budget.get('period', 'monthly'))
        await self._execute(query, params)
    
    async def get_budgets(self, user_id: str) -> List[Dict]:
        rows = await self._execute('SELECT * FROM budgets WHERE user_id = ?', (user_id,))
        return [dict(row) for row in rows]
    
    # Trip methods
    async def store_trip(self, user_id: str, trip: Dict):
        query = '''INSERT INTO trips (user_id, destination, start_date, end_date, budget, travelers)
                   VALUES (?, ?, ?, ?, ?, ?)'''
        params = (
            user_id,
            trip.get('destination', ''),
            trip.get('start_date', ''),
            trip.get('end_date', ''),
            trip.get('budget', 'moderate'),
            trip.get('travelers', 1)
        )
        await self._execute(query, params)
    
    async def get_trips(self, user_id: str, limit: int = 5) -> List[Dict]:
        rows = await self._execute(
            'SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        return [dict(row) for row in rows]
    
    # Recipe methods
    async def store_recipe(self, user_id: str, recipe: Dict):
        query = 'INSERT INTO recipes (user_id, dish, date) VALUES (?, ?, ?)'
        params = (user_id, recipe.get('dish', ''), recipe.get('date', datetime.now().isoformat()))
        await self._execute(query, params)
    
    async def get_recipes(self, user_id: str, limit: int = 10) -> List[Dict]:
        rows = await self._execute(
            'SELECT * FROM recipes WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        return [dict(row) for row in rows]
    
    # Meal plan methods
    async def store_meal_plan(self, user_id: str, plan: Dict):
        query = 'INSERT INTO meal_plans (user_id, preferences, plan) VALUES (?, ?, ?)'
        params = (user_id, json.dumps(plan.get('preferences', {})), plan.get('plan', ''))
        await self._execute(query, params)
    
    async def get_meal_plans(self, user_id: str, limit: int = 5) -> List[Dict]:
        rows = await self._execute(
            'SELECT * FROM meal_plans WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        return [dict(row) for row in rows]
    
    # Portfolio methods
    async def add_to_portfolio(self, user_id: str, holding: Dict):
        query = 'INSERT INTO portfolio (user_id, coin, amount, date) VALUES (?, ?, ?, ?)'
        params = (user_id, holding.get('coin', ''), holding.get('amount', 0), holding.get('date', ''))
        await self._execute(query, params)
    
    async def get_portfolio(self, user_id: str) -> List[Dict]:
        rows = await self._execute('SELECT * FROM portfolio WHERE user_id = ?', (user_id,))
        return [dict(row) for row in rows]
    
    # Crypto query methods
    async def store_crypto_query(self, user_id: str, query: Dict):
        await self._execute(
            'INSERT INTO crypto_queries (user_id, coin, price) VALUES (?, ?, ?)',
            (user_id, query.get('coin', ''), query.get('price', 0))
        )
    
    # Social post methods
    async def store_social_post(self, user_id: str, post: Dict):
        query = '''INSERT INTO social_posts (user_id, platform, content, topic, status)
                   VALUES (?, ?, ?, ?, ?)'''
        params = (
            user_id,
            post.get('platform', 'twitter'),
            post.get('content', ''),
            post.get('topic', ''),
            post.get('status', 'draft')
        )
        await self._execute(query, params)
    
    async def get_social_posts(self, user_id: str, status: str = None, limit: int = 10) -> List[Dict]:
        if status:
            rows = await self._execute(
                'SELECT * FROM social_posts WHERE user_id = ? AND status = ? ORDER BY created_at DESC LIMIT ?',
                (user_id, status, limit)
            )
        else:
            rows = await self._execute(
                'SELECT * FROM social_posts WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
                (user_id, limit)
            )
        return [dict(row) for row in rows]
    
    async def schedule_post(self, user_id: str, schedule: Dict):
        await self._execute(
            'UPDATE social_posts SET scheduled_time = ? WHERE id = ? AND user_id = ?',
            (schedule.get('scheduled_time', ''), schedule.get('post_id'), user_id)
        )
    
    async def get_scheduled_posts(self, user_id: str) -> List[Dict]:
        rows = await self._execute(
            'SELECT * FROM social_posts WHERE user_id = ? AND scheduled_time IS NOT NULL ORDER BY scheduled_time',
            (user_id,)
        )
        return [dict(row) for row in rows]
    
    # Content methods
    async def store_content(self, user_id: str, content: Dict):
        query = 'INSERT INTO content (user_id, topic, content, type, status) VALUES (?, ?, ?, ?, ?)'
        params = (user_id, content.get('topic', ''), content.get('content', ''), 
                 content.get('type', 'article'), content.get('status', 'draft'))
        await self._execute(query, params)
    
    async def get_content(self, user_id: str, limit: int = 10) -> List[Dict]:
        rows = await self._execute(
            'SELECT * FROM content WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        return [dict(row) for row in rows]
    
    # Image prompt methods
    async def store_image_prompt(self, user_id: str, prompt: Dict):
        query = 'INSERT INTO image_prompts (user_id, prompt, status) VALUES (?, ?, ?)'
        params = (user_id, prompt.get('prompt', ''), prompt.get('status', 'generated'))
        await self._execute(query, params)
    
    # Draft methods
    async def store_draft(self, user_id: str, draft: Dict):
        query = 'INSERT INTO drafts (user_id, type, data) VALUES (?, ?, ?)'
        params = (user_id, draft.get('type', 'email'), json.dumps(draft))
        await self._execute(query, params)
    
    async def get_drafts(self, user_id: str, limit: int = 10) -> List[Dict]:
        rows = await self._execute(
            'SELECT * FROM drafts WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        return [dict(row) for row in rows]
    
    # Tweet methods
    async def store_tweet(self, user_id: str, tweet: Dict):
        query = 'INSERT INTO tweets (user_id, text, status, thread_position) VALUES (?, ?, ?, ?)'
        params = (user_id, tweet.get('text', ''), tweet.get('status', 'draft'), tweet.get('thread_position'))
        await self._execute(query, params)
    
    async def get_tweets(self, user_id: str, limit: int = 10) -> List[Dict]:
        rows = await self._execute(
            'SELECT * FROM tweets WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        return [dict(row) for row in rows]
    
    async def get_stats(self) -> Dict:
        """Get database statistics"""
        tables = ['events', 'tasks', 'contacts', 'documents', 'expenses', 'trips', 'portfolio']
        stats = {}
        
        for table in tables:
            try:
                rows = await self._execute(f'SELECT COUNT(*) as count FROM {table}')
                stats[table] = rows[0]['count'] if rows else 0
            except:
                stats[table] = 0
        
        return {"tables": stats, "db_path": self.db_path}
    
    async def shutdown(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.initialized = False
