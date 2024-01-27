import hashlib
import os

from google_auth_oauthlib.flow import Flow

_cred_file = "client_secret_track.json"
root_dir = os.path.abspath(os.path.dirname(__file__))
_CLIENT_SECRET_PATH = os.path.join(root_dir, _cred_file)
_SCOPE = "https://www.googleapis.com/auth/adwords"
# _SERVER = "127.0.0.1
_SERVER = "https://trackocity-endpoint-v5zkx2mbna-em.a.run.app"
_PORT = 5000
# _REDIRECT_URI = f"http://{_SERVER}:{_PORT}/google/oauth2callback"
_REDIRECT_URI = f"{_SERVER}/google/oauth2callback"


def authorize():
    flow = Flow.from_client_secrets_file(_CLIENT_SECRET_PATH, scopes=_SCOPE)
    print(f"_REDIRECT_URI:{_REDIRECT_URI}")
    flow.redirect_uri = _REDIRECT_URI
 
    # Create an anti-forgery state token as described here:
    # https://developers.google.com/identity/protocols/OpenIDConnect#createxsrftoken
    passthrough_val = hashlib.sha256(os.urandom(1024)).hexdigest()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        state=passthrough_val,
        prompt="consent",
        include_granted_scopes="true",
    )

    return {"authorization_url":authorization_url, "passthrough_val":passthrough_val}


    

def oauth2client(passthrough_val, state, code, token):
    if passthrough_val != state:
        message = "State token doesn't match th expected state"
        raise ValueError(message)
    
    flow = Flow.from_client_secrets_file(_CLIENT_SECRET_PATH, scopes=_SCOPE)
    flow.redirect_uri = _REDIRECT_URI

    flow.fetch_token(code=code)
    refresh_token = flow.credentials.refresh_token

    print(f'Refresh token: {refresh_token}')
    return refresh_token