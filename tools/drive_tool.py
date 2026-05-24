"""
Drive Tool - Google Drive integration
"""

import asyncio
from typing import Dict, Any, List, Optional
import os
import io
from datetime import datetime

class DriveTool:
    def __init__(self, config: Dict):
        self.config = config
        self.credentials = config.get('google', {}).get('credentials_file', 'credentials.json')
        self.service = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize Google Drive API"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload
            
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            
            creds = None
            if os.path.exists('drive_token.json'):
                creds = Credentials.from_authorized_user_file('drive_token.json', SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(self.credentials):
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                if creds:
                    with open('drive_token.json', 'w') as token:
                        token.write(creds.to_json())
            
            if creds:
                self.service = build('drive', 'v3', credentials=creds)
                self.initialized = True
                return True
        except ImportError:
            print("Drive libraries not installed")
        except Exception as e:
            print(f"Drive init error: {e}")
        
        return False
    
    async def create_doc(self, title: str, content: str = "", folder_id: str = None) -> Dict:
        """Create a Google Doc"""
        if not self.initialized:
            return {"status": "offline", "title": title}
        
        try:
            from googleapiclient.http import MediaIoBaseUpload
            
            file_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Create empty doc
            doc = await asyncio.to_thread(
                self.service.files().create(body=file_metadata).execute
            )
            
            # If content provided, we'd need Docs API to insert content
            # For now, just create the file
            
            return {"status": "created", "file_id": doc.get('id'), "title": title}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def create_spreadsheet(self, title: str, folder_id: str = None) -> Dict:
        """Create a Google Sheet"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            file_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            file = await asyncio.to_thread(
                self.service.files().create(body=file_metadata).execute
            )
            
            return {"status": "created", "file_id": file.get('id')}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def upload_file(self, file_path: str, folder_id: str = None) -> Dict:
        """Upload a file to Drive"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            from googleapiclient.http import MediaFileUpload
            
            file_name = os.path.basename(file_path)
            file_metadata = {'name': file_name}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = await asyncio.to_thread(
                self.service.files().create(
                    body=file_metadata,
                    media_body=media
                ).execute
            )
            
            return {"status": "uploaded", "file_id": file.get('id')}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def list_files(self, query: str = None, limit: int = 10) -> List[Dict]:
        """List files in Drive"""
        if not self.initialized:
            return []
        
        try:
            params = {
                'pageSize': limit,
                'fields': 'files(id, name, mimeType, createdTime, modifiedTime, size)',
                'orderBy': 'modifiedTime desc'
            }
            
            if query:
                params['q'] = f"name contains '{query}'"
            
            results = await asyncio.to_thread(
                self.service.files().list(**params).execute
            )
            
            return results.get('files', [])
        except Exception as e:
            print(f"List files error: {e}")
            return []
    
    async def search_files(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for files"""
        return await self.list_files(query, limit)
    
    async def delete_file(self, file_id: str) -> Dict:
        """Delete a file"""
        if not self.initialized:
            return {"status": "offline"}
        
        try:
            await asyncio.to_thread(
                self.service.files().delete(fileId=file_id).execute
            )
            return {"status": "deleted"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def shutdown(self):
        """Cleanup"""
        self.initialized = False
        self.service = None
