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
    
    scope = 'user-read-private user-read-email user-read-recently-played user-top-read user-read-currently-playing user-read-playback-state'
    
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


def get_currently_playing(access_token):
    url = 'https://api.spotify.com/v1/me/player/currently-playing'
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = get(url, headers=headers)
        
        if response.status_code == 204:
            return None
        
        if response.status_code == 200:
            data = response.json()
            
            if data and data.get('is_playing'):
                track = data.get('item', {})
                
                return {
                    'track_id': track.get('id'),
                    'track_name': track.get('name'),
                    'artist_name': ', '.join([artist['name'] for artist in track.get('artists', [])]),
                    'artist_ids': [artist['id'] for artist in track.get('artists', [])],
                    'album_name': track.get('album', {}).get('name'),
                    'album_image_url': track.get('album', {}).get('images', [{}])[0].get('url') if track.get('album', {}).get('images') else None,
                    'duration_ms': track.get('duration_ms'),
                    'progress_ms': data.get('progress_ms'),
                    'is_playing': data.get('is_playing'),
                    'external_url': track.get('external_urls', {}).get('spotify')
                }
        
        return None
    except Exception as e:
        print(f"Error fetching currently playing track: {e}")
        return None


def get_top_items(access_token, item_type='tracks', limit=5, time_range='medium_term'):
    if item_type not in ['tracks', 'artists']:
        raise ValueError("item_type must be 'tracks' or 'artists'")
    
    if time_range not in ['short_term', 'medium_term', 'long_term']:
        raise ValueError("time_range must be 'short_term', 'medium_term', or 'long_term'")
    
    url = f'https://api.spotify.com/v1/me/top/{item_type}'
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    params = {
        'limit': limit,
        'time_range': time_range
    }
    
    try:
        response = get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        items = []
        
        for item in data.get('items', []):
            if item_type == 'tracks':
                items.append({
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'artist_name': ', '.join([artist['name'] for artist in item.get('artists', [])]),
                    'album_name': item.get('album', {}).get('name'),
                    'album_image_url': item.get('album', {}).get('images', [{}])[0].get('url') if item.get('album', {}).get('images') else None,
                    'popularity': item.get('popularity'),
                    'external_url': item.get('external_urls', {}).get('spotify')
                })
            else:
                items.append({
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'genres': item.get('genres', []),
                    'popularity': item.get('popularity'),
                    'image_url': item.get('images', [{}])[0].get('url') if item.get('images') else None,
                    'followers': item.get('followers', {}).get('total'),
                    'external_url': item.get('external_urls', {}).get('spotify')
                })
        
        return items
    except Exception as e:
        print(f"Error fetching top {item_type}: {e}")
        return []


def get_top_genres(access_token, limit=5, time_range='medium_term'):
    from collections import Counter
    
    top_artists = get_top_items(access_token, item_type='artists', limit=50, time_range=time_range)
    
    all_genres = []
    for artist in top_artists:
        all_genres.extend(artist.get('genres', []))
    
    genre_counts = Counter(all_genres)
    
    top_genres = genre_counts.most_common(limit)
    
    return [{'genre': genre, 'count': count} for genre, count in top_genres]


def check_and_refresh_token(user):
    if user.token_expires_at and datetime.utcnow() >= user.token_expires_at:
        token_response = refresh_access_token(user.spotify_refresh_token)
        
        if token_response:
            user.spotify_access_token = token_response['access_token']
            user.token_expires_at = calculate_token_expiry(token_response['expires_in'])
            
            from .database import db
            db.session.commit()
            
            return user.spotify_access_token
    
    return user.spotify_access_token
