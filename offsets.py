import requests

class Client:
    def __init__(self):
        try:
            self.offsets = requests.get('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json').json()
            self.clientdll = requests.get('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json').json()
            self.buttons = requests.get('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/buttons.json').json()
        except:
            print('Unable to get offsets.')
            exit()
    def offset(self, a):
        try:
            return self.offsets['client.dll'][a]
        except:
            print(f'Offset {a} not found.')
            exit()
    def get(self, a, b):
        try:
            return self.clientdll["client.dll"]['classes'][a]['fields'][b]
        except Exception as e:
            print(f"Error With Getting Offsets {e}")
            exit()

    def button(self, a):
        try:
            return self.buttons["client.dll"][a]
        except:
            print(f'Offset {a} not found.')
            exit()