from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


class OAuth:
    def __init__(self):
        self.flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email'],
            redirect_uri='redirect_uri')

    def generate_url(self):
        return self.flow.authorization_url()

    def fetch(self, code):
        self.flow.fetch_token(code=code)
        user_info_service = build(
            'oauth2', 'v2', credentials=self.flow.credentials)
        user_info = user_info_service.userinfo().get().execute()

        return user_info
