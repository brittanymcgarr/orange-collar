from app import db

# User model
class User(db.Model):
    # Model columns
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))
    authenticated = db.Column(db.Boolean, default=False)

    primary_address = db.Column(db.String(255))
    primary_lat_coord = db.Column(db.Float(precision=8))
    primary_long_coord = db.Column(db.Float(precision=8))
    secondary_address = db.Column(db.String(255))
    secondary_lat_coord = db.Column(db.Float(precision=8))
    secondary_long_coord = db.Column(db.Float(precision=8))

    primary_phone = db.Column(db.String(11))
    secondary_phone = db.Column(db.String(11))

    allow_mms = db.Column(db.Boolean, default=False)
    allow_sms = db.Column(db.Boolean, default=False)
    allow_voice = db.Column(db.Boolean, default=False)
    
    pets = db.relationship('Pet', backref='user', lazy='dynamic')
    
    last_mms = db.Column(db.DateTime)
    last_sms = db.Column(db.DateTime)
    last_call = db.Column(db.DateTime)
    
    @property
    def is_authenticated(self):
        return True
      
    @property
    def is_active(self):
        return True
    
    @property  
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return self.email
    
    def __repr__(self):
        return '<User %r_%s>' % (self.email, self.id)

# Pet model
class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    species = db.Column(db.String(32))
    color = db.Column(db.String(32))
    breed = db.Column(db.String(32))
    gender = db.Column(db.String(32))
    description = db.Column(db.Text())
    
    indoor_pet = db.Column(db.Boolean(), default=True)
    status = db.Column(db.String(32))
    additional_info = db.Column(db.Text())
    
    owner_notified_last = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    home_address = db.Column(db.String(255))
    home_lat_coord = db.Column(db.Float(precision=8))
    home_long_coord = db.Column(db.Float(precision=8))
    secondary_address = db.Column(db.String(255))
    
    sighting_coords = db.Column(db.Text)
    
    def __repr__(self):
        return '<Pet %r_%s>' % (self.name, self.id)