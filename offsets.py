import requests
from typing import Dict, Any

# Client class for fetching and managing CS2 game offsets
class Client:
    # Base URL for fetching offset data
    BASE_URL = 'https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/'
    
    def __init__(self):
        """Initialize client and fetch offset data"""
        try:
            self.offsets = self._fetch_json('offsets.json')
            self.clientdll = self._fetch_json('client_dll.json') 
            self.buttons = self._fetch_json('buttons.json')
        except Exception as e:
            print(f'Unable to get offsets: {str(e)}')
            exit(1)
            
    def _fetch_json(self, filename: str) -> Dict[str, Any]:
        """Helper method to fetch and parse JSON from URL"""
        response = requests.get(f'{self.BASE_URL}{filename}')
        response.raise_for_status()
        return response.json()

    def offset(self, offset_name: str) -> int:
        """Get offset value by name"""
        try:
            return self.offsets['client.dll'][offset_name]
        except KeyError:
            print(f'Offset {offset_name} not found.')
            exit(1)
            
    def get(self, class_name: str, field_name: str) -> Any:
        """Get client.dll class field value"""
        try:
            return self.clientdll["client.dll"]['classes'][class_name]['fields'][field_name]
        except KeyError as e:
            print(f"Error getting offset: {str(e)}")
            exit(1)

    def button(self, button_name: str) -> int:
        """Get button offset by name"""
        try:
            return self.buttons["client.dll"][button_name]
        except KeyError:
            print(f'Button offset {button_name} not found.')
            exit(1)
