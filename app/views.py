from flask import (render_template, flash, redirect, session, url_for, 
                   request, g, abort, Response)
from flask_login import login_user, logout_user, current_user, login_required
import bcrypt
import os
from app import app, db, lm
from .forms import LoginForm, SignUpForm, ContactForm, NewPetForm
from .models import User, Pet

from twilio.rest import Client

# Get the g session
@app.before_request
def before_request():
    g.user = current_user

# Home
@app.route('/')
@app.route('/index')
def index():
    user = g.user
    
    if user is "" or None:
        user = {'name': None}
    
    return render_template('index.html', title='', user=user)
    
# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        user = User.query.filter_by(email=form.email.data).first() or None
        
        if user is None:
            flash("You are not in our database. Check your email and password or sign up!")
            return redirect(url_for('login'))
        
        if user.password_hash == bcrypt.hashpw(form.password.data.encode('utf-8'), 
                                               user.password_hash.encode('utf-8')):
            
            if "remember_me" in session:
                remember_me = session['remember_me']
                session.pop('remember_me', None)
                        
            login_user(user, remember=remember_me)
            flash("Successfully Logged In. Welcome back, %s!" % g.user.name)
            return redirect(request.args.get('next') or url_for('dashboard'))
        else:
            flash("Password was not valid. Try again or contact an admin.")
            return redirect(url_for('login'))
    
    return render_template('login.html', title='Sign In', form=form)
    
# Logout
@app.route('/logout')
def logout():
    logout_user()
    g.user.authenticated = False
    flash("Logged out")
    return redirect(url_for('index'))
    
# Load the user from the databse
@lm.user_loader
def user_loader(user_id):
    return User.query.filter_by(email=user_id).first()
    
# Sign Up new users
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first() or None
        
        if user is not None:
            flash("That email already exists. Please sign in or contact an admin.")
            return redirect(url_for('login'))
            
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(form.password.data.encode('utf-8'), salt)
        
        user = User(name = form.name.data, 
                    email = form.email.data, 
                    password_hash = password_hash, 
                    primary_phone = form.primary_phone.data,
                    primary_address = form.primary_address.data,
                    secondary_phone = form.secondary_phone.data,
                    allow_mms = form.allow_mms.data,
                    allow_sms = form.allow_sms.data,
                    allow_voice = form.allow_voice.data)
    
        db.session.add(user)
        db.session.commit()
        flash("Successfully created account. Welcome!")
        
        user.authenticated = True
        current_user = user
    
        login_user(user, remember=True)
        return redirect(request.args.get('next') or url_for('dashboard'))
    
    return render_template('signup.html', title='Sign Up', form=form)
    
# View the User Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    if g.user.is_authenticated:
        user = User.query.filter_by(email=g.user.email).first()
        pets = user.pets
        return render_template('dashboard.html', title="Dashboard", 
                                user=user, pets=pets)
    else:
        flash("You need to be logged in to view your dashboard.")
        return redirect(url_for('index'))

# View a User Profile

# Create a Pet Profile for a User's Pet
@app.route('/new_user_pet', methods=['GET', 'POST'])
def new_user_pet():
    form = NewPetForm()
    
    if g.user is not None and g.user.is_authenticated:
        if form.validate_on_submit():
            pet = Pet(name = form.name.data,
                      species = form.species.data,
                      color = form.color.data,
                      breed = form.breed.data,
                      gender = form.gender.data,
                      description = form.description.data,
                      status = form.status.data,
                      additional_info = form.additional_info.data,
                      home_address = form.home_address.data,
                      user_id = g.user.get_id())
            
            db.session.add(pet)
            current_user.pets.append(pet)
            db.session.commit()
            flash("Successfully registered your pet. Good Work!")
            return redirect(request.args.get('next') or url_for('dashboard'))
        
        return render_template('new_user_pet.html', title='Register Your Pet', form=form)
        
    else:
        flash("You need to be logged in to set your own pets or try Report a Sighted Pet")
        return redirect(url_for('index'))

# Create a Pet Profile for a found Pet

# Edit a Pet Profile

# Delete a Pet Profile

# View a Pet Profile
@app.route('/pet_profile/<petID>', methods=['GET', 'POST'])
def pet_profile(petID):
    form = ContactForm()
    
    pet = Pet.query.get(petID) or None
    user = User.query.get(pet.user_id) or None
        
    if request.method == 'POST':
        reportPet(pet.id)
        return render_template('pet.html', title=pet.name, form=form, 
                                pet=pet, user=user)

    if pet is not None:
        return render_template('pet.html', title=pet.name, form=form, 
                                pet=pet, user=user)
    else:
        flash("Pet not found")
        return redirect(url_for('dashboard'))

# Find Pets in the area based on current position

# Find a Pet by Data

# Report a Pet Found
# Reporting a Pet forwards the listing and picture to the owner's email, sms
# mms, or phone through Twilio API
def reportPet(petID):
    pet = Pet.query.get(petID)
    user = User.query.get(pet.user_id)
    
    if user is not None:
        if user.primary_phone is not "":
            message = "Your pet, %s, was reported in the area. Log in to Orange Collar to change your pet's status." % pet.name
            
            #if user.allow_mms and pet.picture is not "":
            #    sendMMS(message, user.primary_phone, pet.picture)
            if user.allow_sms:
                sendSMS(message, user.primary_phone)
            if user.allow_voice:
                sendCall(pet, user, message, user.primary_phone)
            
            flash("The owner is being contacted. Thank you for doing your part!")
        else:
            flash("Could not find the owner\'s contact information. Thank you for trying.")
    else:
        flash("Could not find the owner. Thank you for trying to help.")

# Send SMS
def sendSMS(message="Your pet has been reported.", phone=""):
    if phone != "":
        account_sid = str(os.getenv('TWILIO_SID'))
        auth_token = str(os.getenv('TWILIO_AUTH_TOKEN'))
        local_phone = str(os.getenv('OC_PHONE'))
        
        client = Client(account_sid, auth_token)
    
        client.messages.create(to = "+1%s" % phone,
                               from_ = local_phone,
                               body = message)

# Send MMS
def sendMMS(message="Your pet has been reported.", phone="", picture=""):
    pass

# Send Call
def sendCall(pet, user, message="Your pet has been reported.", phone=""):
    if phone != "":
        account_sid = str(os.getenv('TWILIO_SID'))
        auth_token = str(os.getenv('TWILIO_AUTH_TOKEN'))
        local_phone = str(os.getenv('OC_PHONE'))
        
        url = url_for('calltemplate', petID=pet.id)
        print url
    
        client = Client(account_sid, auth_token)
        call = client.calls.create(to = "+1%s" % phone,
                                   from_ = local_phone,
                                   url = url)

# Create XML
@app.route('/calltemplate.xml/<petID>')
def calltemplate(petID):
    pet = Pet.query.get(petID)
    user = User.query.get(pet.user_id)
    
    if pet is not None and user is not None:
        response_page = render_template('/calltemplate.xml', pet=pet, user=user)
        return Response(response_page, mimetype='text/xml')
    