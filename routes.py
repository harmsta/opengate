from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from .database import db
from .models import User
from . import spotify_service
main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/view')
def view():
    return render_template('view.html', values=User.query.all())

@main.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        session.permanent = True 
        user_name = request.form['name']
        
        found_user = User.query.filter_by(name=user_name).first()
        
        if found_user:
            session['user'] = found_user.name
            session['email'] = found_user.email 
            flash('User already exists, logged in!', 'info')
            
        else:
            new_user = User(name=user_name, email="")
            db.session.add(new_user)
            db.session.commit()
            session['user'] = user_name
            
            flash('New user created and logged in!', 'success')
            
        return redirect(url_for('main.user')) 
    else:
        if 'user' in session:
            flash('Already logged in!', 'info')
            return redirect(url_for('main.user')) 
        
        return render_template('login.html')

@main.route('/user', methods=['POST', 'GET'])
def user():
    email = None
    if 'user' in session:
        user_name = session['user']
        
        if request.method == 'POST':
            email_input = request.form['email']
            session['email'] = email_input
            
            found_user = User.query.filter_by(name=user_name).first()
            
            if found_user:
                found_user.email = email_input
                db.session.commit()
                flash('Email updated and saved!', 'info')
            else:
                 flash('Error: User not found in database.', 'error')
                 
            email = email_input
            
        else:
            if 'email' in session:
                email = session['email']
                
        return render_template('user.html', email=email)
    else:
        return redirect(url_for('main.login'))

@main.route('/logout')
def logout():
    flash(f'You have been logged out.', 'info')       
    session.pop('user', None)
    session.pop('email', None)
    return redirect(url_for('main.login'))


@main.route('/debug_config')
def debug_config():
    """Debug route to check configuration"""
    from flask import current_app, jsonify
    return jsonify({
        'SPOTIFY_CLIENT_ID': current_app.config.get('SPOTIFY_CLIENT_ID'),
        'SPOTIFY_REDIRECT_URI': current_app.config.get('SPOTIFY_REDIRECT_URI'),
        'Has CLIENT_SECRET': bool(current_app.config.get('SPOTIFY_CLIENT_SECRET'))
    })


@main.route('/spotify_login')
def spotify_login():
    """Initiate Spotify OAuth flow with PKCE"""
    # Generate PKCE parameters
    code_verifier = spotify_service.generate_code_verifier()
    code_challenge = spotify_service.generate_code_challenge(code_verifier)
    
    # Generate state for CSRF protection
    import secrets
    state = secrets.token_urlsafe(16)
    
    # Store in session for verification in callback
    session['spotify_state'] = state
    session['code_verifier'] = code_verifier
    
    # Get authorization URL
    auth_url = spotify_service.get_authorization_url(state, code_challenge)
    
    # Debug: Print the redirect URI being used
    from flask import current_app
    print("=" * 80)
    print("DEBUG INFO:")
    print(f"SPOTIFY_CLIENT_ID: {current_app.config.get('SPOTIFY_CLIENT_ID')}")
    print(f"SPOTIFY_REDIRECT_URI: {current_app.config.get('SPOTIFY_REDIRECT_URI')}")
    print(f"Authorization URL: {auth_url}")
    print("=" * 80)
    
    return redirect(auth_url)


@main.route('/callback')
def callback():
    state = request.args.get('state')
    stored_state = session.get('spotify_state')
    
    if not state or state != stored_state:
        flash('Invalid state parameter. Please try again.', 'error')
        return redirect(url_for('main.home'))
    
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        flash(f'Spotify authorization error: {error}', 'error')
        return redirect(url_for('main.home'))
    
    if not code:
        flash('No authorization code received.', 'error')
        return redirect(url_for('main.home'))
    
    code_verifier = session.get('code_verifier')
    
    if not code_verifier:
        flash('Session expired. Please try again.', 'error')
        return redirect(url_for('main.home'))
    
    token_data = spotify_service.exchange_code_for_token(code, code_verifier)
    
    if not token_data:
        flash('Failed to get access token from Spotify.', 'error')
        return redirect(url_for('main.home'))
    
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in')
    
    profile = spotify_service.get_user_profile(access_token)
    
    if not profile:
        flash('Failed to get user profile from Spotify.', 'error')
        return redirect(url_for('main.home'))
    
    spotify_id = profile.get('id')
    display_name = profile.get('display_name', 'Spotify User')
    email = profile.get('email', '')
    
    token_expires_at = spotify_service.calculate_token_expiry(expires_in)
    
    user = User.query.filter_by(spotify_id=spotify_id).first()
    
    if user:
        user.spotify_access_token = access_token
        user.spotify_refresh_token = refresh_token
        user.token_expires_at = token_expires_at
        if email and not user.email:
            user.email = email
        flash('Spotify account connected successfully!', 'success')
    else:
        if 'user' in session:
            user = User.query.filter_by(name=session['user']).first()
            if user:
                user.spotify_id = spotify_id
                user.spotify_access_token = access_token
                user.spotify_refresh_token = refresh_token
                user.token_expires_at = token_expires_at
                if email and not user.email:
                    user.email = email
                flash('Spotify account linked to your profile!', 'success')
            else:
                user = User(name=display_name, email=email)
                user.spotify_id = spotify_id
                user.spotify_access_token = access_token
                user.spotify_refresh_token = refresh_token
                user.token_expires_at = token_expires_at
                db.session.add(user)
                flash('Account created with Spotify!', 'success')
        else:
            user = User(name=display_name, email=email)
            user.spotify_id = spotify_id
            user.spotify_access_token = access_token
            user.spotify_refresh_token = refresh_token
            user.token_expires_at = token_expires_at
            db.session.add(user)
            flash('Account created with Spotify!', 'success')
    
    db.session.commit()
    
    session['user'] = user.name
    session['email'] = user.email
    
    session.pop('spotify_state', None)
    session.pop('code_verifier', None)
    
    return redirect(url_for('main.user'))
 