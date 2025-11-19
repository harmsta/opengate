from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from .__init__ import db 
from .models import User 
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