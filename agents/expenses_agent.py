"""
Expenses Agent - Expense tracking and budget management
"""

import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

class ExpensesAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
        self.sheets_tool = cod3x.tools.get('sheets')
    
    async def initialize(self):
        self.logger.info("Expenses Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process expense-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['add expense', 'log expense', 'spent', 'expense']):
                return await self._add_expense(request, user_id)
            elif any(kw in text_lower for kw in ['budget', 'set budget']):
                return await self._set_budget(request, user_id)
            elif any(kw in text_lower for kw in ['expense report', 'spending report', 'summary']):
                return await self._generate_report(user_id)
            elif any(kw in text_lower for kw in ['expense list', 'my expenses']):
                return await self._list_expenses(user_id)
            elif any(kw in text_lower for kw in ['category', 'categorize']):
                return await self._categorize_expenses(request, user_id)
            else:
                return await self._get_expense_summary(user_id)
        except Exception as e:
            self.logger.error(f"Expenses agent error: {e}")
            return "I had trouble with your expenses. Please try again."
    
    async def _add_expense(self, request: str, user_id: str) -> str:
        """Add a new expense"""
        expense = await self._extract_expense(request)
        
        # Categorize expense
        expense['category'] = await self._categorize_amount(expense.get('description', ''), expense.get('amount', 0))
        
        # Store expense
        await self.cod3x.memory['sqlite'].store_expense(user_id, expense)
        
        # Check budget
        budget_status = await self._check_budget(user_id, expense['category'])
        
        response = f"💰 Expense logged: ${expense.get('amount', 0):.2f} for {expense.get('description', 'item')}"
        if budget_status:
            response += f"\n⚠️ {budget_status}"
        
        # Sync to Google Sheets if available
        if self.sheets_tool:
            try:
                await self.sheets_tool.append_row('expenses', [
                    datetime.now().isoformat(),
                    expense.get('amount', 0),
                    expense.get('category', 'other'),
                    expense.get('description', '')
                ])
            except:
                pass
        
        return response
    
    async def _extract_expense(self, request: str) -> Dict:
        """Extract expense details from natural language"""
        if self.model:
            prompt = f"""Extract expense details from: {request}
            Return JSON: {{"amount": number, "description": "item description", "date": "YYYY-MM-DD", "payment_method": "cash/card/other"}}"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return json.loads(response.text)
            except:
                pass
        
        # Fallback extraction
        expense = {
            "amount": 0,
            "description": "Unknown expense",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "payment_method": "other"
        }
        
        text = request.lower()
        
        # Extract amount
        import re
        amount_match = re.search(r'\$?(\d+\.?\d*)', text)
        if amount_match:
            expense['amount'] = float(amount_match.group(1))
        
        # Extract description
        for prefix in ['spent', 'add expense', 'log expense', 'expense']:
            if prefix in text:
                parts = text.split(prefix, 1)
                if len(parts) > 1:
                    desc = parts[1].strip()
                    # Remove amount from description
                    desc = re.sub(r'\$?\d+\.?\d*', '', desc).strip()
                    expense['description'] = desc.title() if desc else "Unknown expense"
                break
        
        # Payment method
        if 'card' in text:
            expense['payment_method'] = 'card'
        elif 'cash' in text:
            expense['payment_method'] = 'cash'
        
        return expense
    
    async def _categorize_amount(self, description: str, amount: float) -> str:
        """Categorize expense based on description"""
        if self.model:
            prompt = f"Categorize this expense into one category: Food, Transport, Entertainment, Bills, Shopping, Health, Other\n\nDescription: {description}\nAmount: ${amount}\n\nReturn just the category name."
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return response.text.strip()
            except:
                pass
        
        # Keyword-based categorization
        categories = {
            'food': ['food', 'restaurant', 'lunch', 'dinner', 'breakfast', 'coffee', 'grocery'],
            'transport': ['uber', 'taxi', 'gas', 'fuel', 'bus', 'train', 'transport'],
            'entertainment': ['movie', 'game', 'netflix', 'spotify', 'concert', 'entertainment'],
            'bills': ['rent', 'electricity', 'water', 'internet', 'phone', 'bill', 'subscription'],
            'shopping': ['amazon', 'clothes', 'shoes', 'shop', 'buy', 'purchase'],
            'health': ['doctor', 'medicine', 'gym', 'health', 'fitness']
        }
        
        desc_lower = description.lower()
        for category, keywords in categories.items():
            if any(kw in desc_lower for kw in keywords):
                return category
        
        return 'other'
    
    async def _set_budget(self, request: str, user_id: str) -> str:
        """Set budget for categories"""
        budget_info = await self._extract_budget(request)
        
        await self.cod3x.memory['sqlite'].set_budget(user_id, budget_info)
        
        return f"📊 Budget set: ${budget_info.get('amount', 0):.2f} for {budget_info.get('category', 'all categories')}"
    
    async def _extract_budget(self, request: str) -> Dict:
        """Extract budget details"""
        budget = {"amount": 0, "category": "all", "period": "monthly"}
        
        text = request.lower()
        
        import re
        amount_match = re.search(r'\$?(\d+\.?\d*)', text)
        if amount_match:
            budget['amount'] = float(amount_match.group(1))
        
        if 'food' in text:
            budget['category'] = 'food'
        elif 'transport' in text:
            budget['category'] = 'transport'
        elif 'entertainment' in text:
            budget['category'] = 'entertainment'
        
        if 'weekly' in text:
            budget['period'] = 'weekly'
        elif 'yearly' in text or 'annual' in text:
            budget['period'] = 'yearly'
        
        return budget
    
    async def _check_budget(self, user_id: str, category: str) -> str:
        """Check budget status"""
        budgets = await self.cod3x.memory['sqlite'].get_budgets(user_id)
        
        for budget in budgets:
            if budget.get('category') == category or budget.get('category') == 'all':
                expenses = await self.cod3x.memory['sqlite'].get_expenses(user_id, category)
                total = sum(e.get('amount', 0) for e in expenses)
                
                if total > budget.get('amount', 0) * 0.8:
                    remaining = budget.get('amount', 0) - total
                    return f"Budget alert: ${remaining:.2f} remaining in {category} budget"
        
        return ""
    
    async def _generate_report(self, user_id: str) -> str:
        """Generate expense report"""
        expenses = await self.cod3x.memory['sqlite'].get_expenses(user_id)
        
        if not expenses:
            return "📊 No expenses recorded yet. Start by saying 'add expense $50 for lunch'"
        
        # Calculate totals by category
        by_category = {}
        total = 0
        
        for expense in expenses:
            category = expense.get('category', 'other')
            amount = expense.get('amount', 0)
            by_category[category] = by_category.get(category, 0) + amount
            total += amount
        
        response = "📊 **Expense Report**\n\n"
        response += f"Total: ${total:.2f}\n\n"
        response += "**By Category:**\n"
        
        # Sort by amount
        sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
        for category, amount in sorted_cats:
            percentage = (amount / total * 100) if total > 0 else 0
            bar = "█" * int(percentage / 5)
            response += f"• {category.title()}: ${amount:.2f} ({percentage:.1f}%)\n"
            response += f"  {bar}\n"
        
        return response
    
    async def _list_expenses(self, user_id: str) -> str:
        """List recent expenses"""
        expenses = await self.cod3x.memory['sqlite'].get_expenses(user_id, limit=10)
        
        if not expenses:
            return "💰 No expenses recorded. Say 'add expense [amount] for [description]'"
        
        response = "💰 **Recent Expenses:**\n\n"
        for exp in expenses:
            response += f"• ${exp.get('amount', 0):.2f} - {exp.get('description', 'Unknown')}"
            response += f" [{exp.get('category', 'other')}] - {exp.get('date', '')}\n"
        
        return response
    
    async def _categorize_expenses(self, request: str, user_id: str) -> str:
        """Recategorize expenses"""
        return "📂 Expense categories updated. Use 'expense report' to see breakdown."
    
    async def _get_expense_summary(self, user_id: str) -> str:
        """Get quick expense summary"""
        expenses = await self.cod3x.memory['sqlite'].get_expenses(user_id)
        
        if not expenses:
            return "💰 No expenses yet. Track spending by saying 'add expense [amount]'"
        
        total = sum(e.get('amount', 0) for e in expenses)
        count = len(expenses)
        avg = total / count if count > 0 else 0
        
        return f"💰 **Summary:** {count} expenses, total ${total:.2f}, avg ${avg:.2f}"
    
    async def shutdown(self):
        pass
