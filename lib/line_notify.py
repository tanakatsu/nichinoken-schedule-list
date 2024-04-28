import requests


class LineNotify:
    def __init__(self, token: str):
        self.token = token

    def send_message(self, message: str) -> None:
        API_URL = 'https://notify-api.line.me/api/notify'
        headers = {'Authorization': f'Bearer {self.token}'}
        data = {'message': f'message: {message}'}
        requests.post(API_URL, headers=headers, data=data)
