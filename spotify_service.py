from dotenv import load_dotenv
import os
import base64
import hashlib
import secrets
from requests import post, get
import json
from datetime import datetime, timedelta
from flask import current_app

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")


def get_authorization_header():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes).decode('utf-8'))
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token   

token = get_authorization_header()


def generate_code_verifier():
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')


def generate_code_challenge(code_verifier):
    challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')


def get_authorization_url(state, code_challenge):
    client_id_val = current_app.config['SPOTIFY_CLIENT_ID']
    redirect_uri = current_app.config['SPOTIFY_REDIRECT_URI']
    
    scope = 'user-read-private user-read-email user-read-recently-played user-top-read'
    
    auth_params = {
        'client_id': client_id_val,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'state': state,
        'scope': scope,
        'code_challenge_method': 'S256',
        'code_challenge': code_challenge
    }
    
    auth_url = 'https://accounts.spotify.com/authorize?'
    from urllib.parse import quote
    auth_url += '&'.join([f'{key}={quote(str(value))}' for key, value in auth_params.items()])
    
    return auth_url


def exchange_code_for_token(code, code_verifier):
    client_id_val = current_app.config['SPOTIFY_CLIENT_ID']
    redirect_uri = current_app.config['SPOTIFY_REDIRECT_URI']
    
    token_url = 'https://accounts.spotify.com/api/token'
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id_val,
        'code_verifier': code_verifier
    }
    
    try:
        response = post(token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error exchanging code for token: {e}")
        return None


def refresh_access_token(refresh_token_val):
    client_id_val = current_app.config['SPOTIFY_CLIENT_ID']
    
    token_url = 'https://accounts.spotify.com/api/token'
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token_val,
        'client_id': client_id_val
    }
    
    try:
        response = post(token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None


def get_user_profile(access_token):
    profile_url = 'https://api.spotify.com/v1/me'
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = get(profile_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return None


def calculate_token_expiry(expires_in):
    return datetime.utcnow() + timedelta(seconds=expires_in)
