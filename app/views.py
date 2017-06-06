import bcrypt
import os
import datetime
import requests
import json
import time

from flask_login import login_user, logout_user, current_user, login_required
from flask import (render_template, flash, redirect, session, url_for, 
                   request, g, abort, Response)
from werkzeug.utils import secure_filename

from app import app, db, lm
from .forms import (LoginForm, SignUpForm, ContactForm, NewPetForm, 
                    EditForm, ImageForm, LocationForm)
from .models import User, Pet, Alert

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# Get the g session
@app.before_request
def before_request():
    g.user = current_user

# Home
@app.route('/')
@app.route('/index')
def index():
    user = g.user
    
    if user is None:
        user = {'name': None}
        
    form = LocationForm()
    
    return render_template('index.html', title='', user=user, form=form)
    
# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))

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
                        
            login_user(user, remember = remember_me)
            flash("Successfully Logged In. Welcome back, %s!" % g.user.name)
            return redirect(url_for('dashboard'))
        else:
            flash("Password was not valid. Try again or contact an admin.")
            return redirect(url_for('login'))
    
    return render_template('login.html', title='Sign In', form=form)
    
# Logout
@app.route('/logout')
def logout():
    logout_user()
    
    flash("Logged out")
    return redirect(url_for('index'))
    
# Load the user from the databse
@lm.user_loader
def user_loader(email):
    return User.query.filter_by(email=email).first() or None
    
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
                    allow_mms = form.allow_mms.data,
                    allow_sms = form.allow_sms.data,
                    allow_voice = form.allow_voice.data,
                    pet_watch = form.pet_watch.data,
                    last_mms = datetime.datetime.now(),
                    last_sms = datetime.datetime.now(),
                    last_call = datetime.datetime.now())
                    
        db.session.add(user)
        db.session.commit()
        
        getUserCoords(user)
        
        flash("Successfully created account. Welcome!")
    
        user.authenticated = True
        login_user(user)
        return redirect(url_for('dashboard'))
    
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
        return render_template('dashboard.html', title="Dashboard",
                                user={"name":None}, pets=[])

# Edit a User Profile
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        form = EditForm()
        user = User.query.get(g.user.id)
        
        if g.user.is_authenticated and user is not None:
            if form.validate_on_submit():
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(form.password.data.encode('utf-8'), salt)
        
                user.name = form.name.data
                user.password_hash = password_hash
                user.primary_phone = form.primary_phone.data
                user.secondary_phone = form.secondary_phone.data
                user.primary_address = form.primary_address.data
                user.secondary_address = form.secondary_address.data
                user.allow_mms = form.allow_mms.data
                user.allow_sms = form.allow_sms.data
                user.allow_voice = form.allow_voice.data
                user.pet_watch = form.pet_watch.data
                
                db.session.add(user)
                db.session.commit()
                
                getUserCoords(user)
                
                flash('Updated profile information.')
                return redirect(url_for('dashboard'))
    else:
        form = EditForm()
    
    return render_template('edit_user.html', title="Edit User", user=g.user, form=form)

# Create a Pet Profile for a User's Pet
@app.route('/new_user_pet', methods=['GET', 'POST'])
def new_user_pet():
    form = NewPetForm()
    
    if g.user is not None and g.user.is_authenticated:
        if form.validate_on_submit():
            pet = Pet(name = form.name.data,
                      species = form.species.data.lower(),
                      color = form.color.data,
                      breed = form.breed.data,
                      gender = form.gender.data,
                      description = form.description.data,
                      status = form.status.data,
                      home_address = form.home_address.data,
                      user_id = g.user.get_id())
            
            db.session.add(pet)
            current_user.pets.append(pet)
            db.session.commit()
            
            getPetCoords(pet)
            
            flash("Successfully registered your pet. Good Work!")
            return redirect(request.args.get('next') or url_for('dashboard'))
        
        return render_template('new_user_pet.html', title='Register Your Pet', form=form)
        
    else:
        flash("You need to be logged in to set your own pets or try Report a Sighted Pet")
        return redirect(url_for('index'))
        
# Edit the user's pet
@app.route('/editpet/<petID>', methods=['GET', 'POST'])
def editpet(petID):
    form = NewPetForm()
    
    if request.method == 'POST' and g.user.is_authenticated:
        pet = Pet.query.get(petID) or None
        
        if pet not in g.user.pets:
            pet = None
            flash("You may only edit your own pets.")
        
        if g.user.is_authenticated and pet is not None:
            if form.validate_on_submit():
                pet.name = form.name.data
                pet.species = form.species.data.lower()
                pet.color = form.color.data
                pet.breed = form.breed.data
                pet.gender = form.gender.data
                pet.description = form.description.data
                pet.indoor_pet = form.indoor_pet.data
                pet.status = form.status.data
                pet.home_address = form.home_address.data

                db.session.add(pet)
                db.session.commit()
                
                getPetCoords(pet)
                
                if pet.status == "Lost":
                    sendPetWatch(pet.id)
                
                flash('Updated pet profile information.')
                return redirect(url_for('pet_profile', petID=petID))
    
    return render_template('edit_pet.html', title="Edit User", petID=petID, form=form)

# Upload an image for the pet
@app.route('/image-upload/<petID>', methods=['GET', 'POST'])
def image_upload(petID):
    if request.method == 'POST' and g.user.is_authenticated:
        form = ImageForm(request.form)
        
        if form.validate_on_submit():
            pet = Pet.query.get(petID) or None
            
            if pet is not None and pet in g.user.pets:
                image_file = request.files['file']
                filename = os.path.join(app.config['IMAGES_DIR'], secure_filename(image_file.filename))
                image_file.save(filename)
                pet.picture = image_file.filename
                
                db.session.add(pet)
                db.session.commit()
                
                flash('Saved %s' % os.path.basename(filename), 'success')
                return redirect(url_for('pet_profile', petID=pet.id))
        else:
            flash("Unable to locate the requested pet to upload file.")
            return redirect(url_for('dashboard'))
    else:
        form = ImageForm()

    return render_template('image_upload.html', title="Upload a Picture", petID=petID, form=form)

# Create a Pet Profile for a found Pet

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
            message = "Your %s, %s, was sighted in the area. Log in to Orange Collar to change your pet's status." % (pet.species, pet.name)
            time = datetime.datetime.now()
            
            if user.allow_mms:
                sendMMS(message, user.primary_phone, pet.picture)
            if user.allow_sms:
                if (user.last_sms + datetime.timedelta(minutes = 10)) < time:
                    sendSMS(message, user.primary_phone)
                
            if user.allow_voice:
                if (user.last_call + datetime.timedelta(minutes = 10)) < time:
                    sendCall(pet, user, message, user.primary_phone)
            
            user.last_mms = time
            user.last_sms = time
            user.last_call = time
            db.session.commit()
            
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
def sendMMS(message="Your pet has been reported.", phone="", picture="", imageflag=True):
    if picture == "" or picture == None:
        image = 'http://orange-collar.herokuapp.com/static/orangecollar.png'
    elif imageflag:
        image = 'http://orange-collar.herokuapp.com/static/images/%s' % picture
    else:
        image = picture
    
    if phone != "":
        account_sid = str(os.getenv('TWILIO_SID'))
        auth_token = str(os.getenv('TWILIO_AUTH_TOKEN'))
        local_phone = str(os.getenv('OC_PHONE'))
        
        client = Client(account_sid, auth_token)
        client.messages.create(to = "+1%s" % phone,
                               from_ = local_phone,
                               body = message,
                               media_url=[image])

# Send Call
def sendCall(pet, user, message="Your pet has been reported.", phone=""):
    if phone != "":
        account_sid = str(os.getenv('TWILIO_SID'))
        auth_token = str(os.getenv('TWILIO_AUTH_TOKEN'))
        local_phone = str(os.getenv('OC_PHONE'))
        
        url = url_for('calltemplate', petID=pet.id)
        url = "http://orange-collar.herokuapp.com" + url

        client = Client(account_sid, auth_token)
        call = client.calls.create(to = "+1%s" % phone,
                                   from_ = local_phone,
                                   url = url)

# Create XML
@app.route('/calltemplate.xml/<petID>', methods=['GET', 'POST'])
def calltemplate(petID):
    pet = Pet.query.get(petID)
    user = User.query.get(pet.user_id)
    
    if pet is not None and user is not None:
        response_page = render_template('/calltemplate.xml', pet=pet, user=user)
        return Response(response_page, mimetype='text/xml')
    
# Check permissible file types
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Get pet latitude and longitude
# Translate the given address to a lat, long coordinate from Google API
# Offers 0.000000, 0.0000000 if lat long were not found
def getPetCoords(pet):
    lines = pet.home_address.replace(' ', "").split(',')
    
    if len(lines) >= 3:
        url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s,%s,%s" % (lines[0], lines[1], lines[2])
        
        response = requests.get(url)
        resp_json = response.json()
        
        if len(resp_json['results']) > 0:
            pet.home_lat_coord = resp_json['results'][0]['geometry']['location']['lat']
            pet.home_long_coord = resp_json['results'][0]['geometry']['location']['lng']
        else:
            pet.home_address = 0.000000
            pet.home_long_coord = 0.000000
            
        db.session.add(pet)
        db.session.commit()
        
        flash("Updated Pet's home coordinates")
    else:
        flash("Unable to interpret the address. Separate street, city, and state with commas.")
        
# Get the user's coordinates
def getUserCoords(user):
    lines = user.primary_address.replace(' ', "").split(',')
    
    if len(lines) >= 3:
        url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s,%s,%s" % (lines[0], lines[1], lines[2])
        
        response = requests.get(url)
        resp_json = response.json()
        
        if len(resp_json['results']) > 0:
            user.primary_lat_coord = resp_json['results'][0]['geometry']['location']['lat']
            user.primary_long_coord = resp_json['results'][0]['geometry']['location']['lng']
        else:
            user.primary_lat_coord = 0.000000
            user.primary_long_coord = 0.000000
            
        db.session.add(user)
        db.session.commit()
        
        flash("Updated user's coordinates")
    else:
        flash("Unable to interpret the address to coordinates. Separate street, city, and state with commas.")
        
# Get the input coordinates
def getSearchCoords(address=""):
    lines = address.replace(' ', "").split(',')
    coords = {}
    
    if len(lines) >= 3:
        url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s,%s,%s" % (lines[0], lines[1], lines[2])
        
        response = requests.get(url)
        resp_json = response.json()
        
        if len(resp_json['results']) > 0:
            coords['lat'] = resp_json['results'][0]['geometry']['location']['lat']
            coords['long'] = resp_json['results'][0]['geometry']['location']['lng']
        else:
            coords['lat'] = 0.000000
            coords['long'] = 0.000000
    else:
        flash("Unable to interpret the address. Separate street, city, and state with commas.")
    
    return coords
    
# Get the nearest pets by coordinates
def getPetsByCoords(coords):
    if 'lat' in coords.keys() and 'long' in coords.keys():
        pets = Pet.query.filter((Pet.home_lat_coord >= (coords['lat'] - 0.1)) &
                                (Pet.home_lat_coord <= (coords['lat'] + 0.1)) &
                                (Pet.home_long_coord >= (coords['long'] - 0.1)) &
                                (Pet.home_long_coord <= (coords['long'] + 0.1))).all()
        
        return pets
    else:
        return []
    
# Format the Pet coordinates for Google Maps
def formatPetCoords(petCoords):
    coords = []
    
    for pet in petCoords:
        image = "<a href=\'%s\'><img src=\'/static/images/%s\' style=\'max-height:100px;max-width:100px;\'/></a>" % (url_for('pet_profile', petID=pet.id), pet.picture)
        coord = (pet.home_lat_coord, pet.home_long_coord, image)
        coords.append(coord)
        
    return coords

# Get the requesting User's Coordinates
@app.route('/locate', methods=['GET', 'POST'])
def locate():
    form = LocationForm()
    pets = []
    
    if request.method == 'POST':
        if form.validate_on_submit():
            coords = getSearchCoords(form.address.data)
            
            if coords['lat'] > 0.000000:
                pets = getPetsByCoords(coords)
                petCoords = formatPetCoords(pets)
                
                return render_template('location.html', title="Found Pets", pets=pets, petCoords=petCoords, form=form)
            else:
                flash("Could not find coordinates. Make sure the street address, city, and state are separated by commas.")
                return redirect(url_for('index'))
                
    flash("Please enter an address separated by commas.")
    return redirect(url_for('index'))
    
# Pet Watch
# Alert nearby Pet Watchers that an animal has been reported missing in their area
def sendPetWatch(petID):
    pet = Pet.query.get(petID) or None
    
    if pet is not None:
        coords = {'lat': pet.home_lat_coord, 'long': pet.home_long_coord}
        
        watchers = User.query.filter((User.primary_lat_coord >= (coords['lat'] - 0.1)) &
                                    (User.primary_lat_coord <= (coords['lat'] + 0.1)) &
                                    (User.primary_long_coord >= (coords['long'] - 0.1)) &
                                    (User.primary_long_coord <= (coords['long'] + 0.1)))
                                    
        message = "Calling all Watchdogs! A %s, %s, has been reported missing in the area. Please head to Orange Collar to view a description of %s. Thank you for watching out for this pet." % (pet.species, pet.name, pet.name)

        for watcher in watchers:
            if watcher.pet_watch:
                if watcher.allow_mms:
                    sendMMS(message, watcher.primary_phone, pet.picture)
                elif watcher.allow_sms:
                    sendSMS(message, watcher.primary_phone)

                if watcher.allow_voice:
                    sendCall(pet, watcher, message, watcher.primary_phone)

# Incoming voice
# Incoming voice should return a polite redirect to website
@app.route('/incomingcall', methods=['GET', 'POST'])
def incomingcall():
    if request.method == 'POST':
        response_page = render_template('/incomingcall.xml')
        return Response(response_page, mimetype='text/xml')
    else:
        return redirect(url_for('index'))

# Incoming MMS
# Incoming MMS/SMS with image attachments should be forwarded to the owners of 
# lost pets
@app.route('/incomingmessage', methods=['GET', 'POST'])
def incomingmessage():
    number = request.values.get('From', None)
    number = number[2:]
    
    alert = Alert.query.filter(Alert.number == str(number)).first() or None
    
    if alert is None:
        alert = Alert()
        alert.number = str(number)
        alert.message = ""
        alert.media = ""
    
    message = request.values.get('Body', None).strip().lower()
    
    if message != None and message != "":
        alert.message = message
    
    # Just get the first image, if multiple
    if request.values.get('NumMedia', None) > 0:
        alert.media = request.values.get('MediaUrl0', None)
        # Figure out if Twilio already prevents illicit images
        # Otherwise, implement through Google Cloud Vision

    addrstr = u"address"
    
    if message != "" and message.find(addrstr) > -1:
        if alert.time_issued is None or (alert.time_issued + datetime.timedelta(minutes = 3) < datetime.datetime.now()):
            response = "Thank you for doing your part. The pet is being compared with our database of lost pets, and if an owner is matched, we will contact them shortly."
            alert.time_issued = datetime.datetime.now()
        else:
            response = "Thank you for doing your part!"
    else:
        response = "Thank you for contacting Orange Collar. Text the street address and animal to report a sighted pet and include semi-colons. e.g. \'address:123 Example Street, San Francisco, CA; animal: Cat; description: Fluffy and black;\'. You can also include a picture. Thank you for doing your part!"

    if ((alert.media != "" and alert.media is not None) and 
        (alert.message != "" and alert.message is not None)):
        searchPetsSMS(alert.message, alert.media)
        alert.message = ""
        alert.media = ""
        
    db.session.add(alert)
    db.session.commit()
        
    responder = MessagingResponse()
    responder.message(response)
    return str(responder)
    
# Search the Pets database for the message
def searchPetsSMS(message, media):
    print "Message: %s\nMedia: %s" % (message, media)
    messages = message.split(';')
    params = {}
    
    for field in messages:
        if field.find(':') > -1:
            tags = field.split(':')
            
            if len(tags) == 2:
                key = tags[0].strip().lstrip()
                value = tags[1].strip().lstrip()
                
                params[key] = value
    
    addr_pets = []
    anml_pets = []
    anmlstr = "animal"
    addrstr = "address"
    
    if addrstr in params.keys():
        alert_message = "An animal was reported at %s, matching your lost pet\'s species." % (params[addrstr].upper())
        coords = getSearchCoords(params[addrstr])
        addr_pets = getPetsByCoords(coords)
    else:
        # Want to limit this to helpful information
        return False
    
    if anmlstr in params.keys():
        anml_pets = Pet.query.filter(Pet.species == params[anmlstr], Pet.status == 'Lost').all()
        
    for animal in addr_pets:
        if animal.species == params[anmlstr] and animal.status == "Lost":
            anml_pets.append(animal)
            
    anml_pets = list(set(anml_pets))
    
    for pet in anml_pets:
        if pet.user_id:
            contactUser(pet.user_id, pet, alert_message, media)
    
    return True
    
# Contact the User through any channel applied
def contactUser(user_id, pet, message, media=""):
    user = User.query.get(user_id)
    
    if user.allow_mms:
        sendMMS(message=message, phone=user.primary_phone, picture=media, imageflag=False)
    if not user.allow_mms and user.allow_sms:
        sendSMS(message=message, phone=user.primary_phone)
    if user.allow_voice:
        sendCall(pet, user, message, user.primary_phone)
    