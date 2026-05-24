"""
Sheets Tool - Google Sheets integration
"""

import asyncio
from typing import Dict, Any, List, Optional
import os

class SheetsTool:
    def __init__(self, config: Dict):
        self.config = config
        self.credentials = config.get('google', {}).get('credentials_file', 'credentials.json')
        self.service = None
        self.initialized = False
        self.spreadsheet_id = config.get('google', {}).get('spreadsheet_id')
    
    async def initialize(self):
        """Initialize Google Sheets API"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            
            creds = None
            if os.path.exists('sheets_token.json'):
                creds = Credentials.from_authorized_user_file('sheets_token.json', SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(self.credentials):
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                if creds:
                    with open('sheets_token.json', 'w') as token:
                        token.write(creds.to_json())
            
            if creds:
                self.service = build('sheets', 'v4', credentials=creds)
                
                # Create default spreadsheet if none exists
                if not self.spreadsheet_id:
                    spreadsheet = await self._create_default_spreadsheet()
                    self.spreadsheet_id = spreadsheet.get('spreadsheetId')
                
                self.initialized = True
                return True
        except ImportError:
            print("Sheets libraries not installed")
        except Exception as e:
            print(f"Sheets init error: {e}")
        
        return False
    
    async def _create_default_spreadsheet(self) -> Dict:
        """Create default spreadsheet with sheets for different data types"""
        try:
            spreadsheet = await asyncio.to_thread(
                self.service.spreadsheets().create(body={
                    'properties': {'title': 'Cod3x Data'},
                    'sheets': [
                        {'properties': {'title': 'expenses'}},
                        {'properties': {'title': 'tasks'}},
                        {'properties': {'title': 'contacts'}},
                        {'properties': {'title': 'notes'}}
                    ]
                }).execute
            )
            
            # Add headers
            headers_data = {
                'expenses': [['Date', 'Amount', 'Category', 'Description']],
                'tasks': [['Task', 'Status', 'Priority', 'Due Date']],
                'contacts': [['Name', 'Email', 'Phone', 'Company']],
                'notes': [['Title', 'Content', 'Created', 'Tags']]
            }
            
            for sheet_name, headers in headers_data.items():
                await self.append_row(sheet_name, headers[0])
            
            return spreadsheet
        except Exception as e:
            print(f"Create spreadsheet error: {e}")
            return {}
    
    async def append_row(self, sheet_name: str, row_data: List) -> Dict:
        """Append a row to a sheet"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            body = {'values': [row_data]}
            
            result = await asyncio.to_thread(
                self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A:Z',
                    valueInputOption='RAW',
                    body=body
                ).execute
            )
            
            return {"status": "appended", "rows": result.get('updates', {}).get('updatedRows', 0)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def read_sheet(self, sheet_name: str, range_spec: str = None) -> List[List]:
        """Read data from a sheet"""
        if not self.initialized:
            return []
        
        try:
            if not range_spec:
                range_spec = f'{sheet_name}!A:Z'
            
            result = await asyncio.to_thread(
                self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_spec
                ).execute
            )
            
            return result.get('values', [])
        except Exception as e:
            print(f"Read sheet error: {e}")
            return []
    
    async def update_cell(self, sheet_name: str, cell: str, value: Any) -> Dict:
        """Update a specific cell"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            body = {'values': [[value]]}
            
            await asyncio.to_thread(
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!{cell}',
                    valueInputOption='RAW',
                    body=body
                ).execute
            )
            
            return {"status": "updated"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def clear_sheet(self, sheet_name: str) -> Dict:
        """Clear a sheet"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            await asyncio.to_thread(
                self.service.spreadsheets().values().clear(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A:Z'
                ).execute
            )
            
            return {"status": "cleared"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def create_sheet(self, sheet_name: str) -> Dict:
        """Create a new sheet tab"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            await asyncio.to_thread(
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={
                        'requests': [{
                            'addSheet': {
                                'properties': {'title': sheet_name}
                            }
                        }]
                    }
                ).execute
            )
            
            return {"status": "created", "sheet": sheet_name}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def shutdown(self):
        """Cleanup"""
        self.initialized = False
        self.service = None
