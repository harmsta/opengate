from .database import db

class User(db.Model):
    __tablename__ = 'User'
    
    # Primary Key
    user_id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    
    # Spotify OAuth columns
    spotify_id = db.Column(db.String(100), unique=True, nullable=True)
    spotify_access_token = db.Column(db.String(512), nullable=True)
    spotify_refresh_token = db.Column(db.String(512), nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    
    # ORM Relationships
    listening_logs = db.relationship("Listening_Log", backref="user", lazy=True)
    track_tags = db.relationship("Track_Tag", backref="user_tagger", lazy=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email
        
class Genre(db.Model):
    __tablename__ = 'Genre'
    
    # Primary Key
    primary_genre_id = db.Column(db.Integer, primary_key=True)
    primary_genre_name = db.Column(db.String(50), unique=True)
    
    # ORM Relationships
    artists = db.relationship("Artist", backref="primary_genre", lazy=True)

    def __init__(self, primary_genre_name):
        self.primary_genre_name = primary_genre_name
        
class Artist(db.Model):
    __tablename__ = 'Artist'
    
    # Primary Key
    spotify_artist_id = db.Column(db.String(50), primary_key=True)
    artist_name = db.Column(db.String(50))
    popularity_score = db.Column(db.Integer)
    image_url = db.Column(db.String(256))
    
    # Foreign Key to Genre
    primary_genre_id = db.Column(db.Integer, db.ForeignKey('Genre.primary_genre_id'), nullable=False)
    
    # ORM Relationships
    tracks = db.relationship("Track", backref="artist", lazy=True)

    def __init__(self, spotify_artist_id, artist_name, popularity_score, primary_genre_id, image_url=None):
        self.spotify_artist_id = spotify_artist_id
        self.artist_name = artist_name
        self.popularity_score = popularity_score
        self.primary_genre_id = primary_genre_id
        self.image_url = image_url

class Track(db.Model):
    __tablename__ = 'Track'
    
    # Primary Key 
    spotify_track_id = db.Column(db.String(50), primary_key=True)
    track_album_name = db.Column(db.String(50))
    
    # Foreign Key to Artist
    spotify_artist_id = db.Column(db.String(50), db.ForeignKey('Artist.spotify_artist_id'), nullable=False)
    
    # ORM Relationships
    listening_logs = db.relationship("Listening_Log", backref="track", lazy=True)
    track_tags = db.relationship("Track_Tag", backref="track_tagged", lazy=True)

    def __init__(self, spotify_track_id, track_album_name, spotify_artist_id):
        self.spotify_track_id = spotify_track_id
        self.track_album_name = track_album_name
        self.spotify_artist_id = spotify_artist_id
        
class Tag(db.Model):
    __tablename__ = 'Tag'
    
    # Primary Key
    tag_id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(50), unique=True)
    
    # ORM Relationships
    track_tags = db.relationship("Track_Tag", backref="tag", lazy=True)

    def __init__(self, tag_name):
        self.tag_name = tag_name
        
class Listening_Log(db.Model):
    __tablename__ = 'Listening_Log'
    
    # Primary Key
    log_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    play_duration = db.Column(db.Integer)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    spotify_track_id = db.Column(db.String(50), db.ForeignKey('Track.spotify_track_id'), nullable=False)

    def __init__(self, user_id, spotify_track_id, timestamp, play_duration):
        self.user_id = user_id
        self.spotify_track_id = spotify_track_id
        self.timestamp = timestamp
        self.play_duration = play_duration
        
class Track_Tag(db.Model):
    __tablename__ = 'Track_Tag'
    
    # Primary Key
    track_tag_id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys 
    spotify_track_id = db.Column(db.String(50), db.ForeignKey('Track.spotify_track_id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('Tag.tag_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False) # User who applied the tag

    def __init__(self, spotify_track_id, tag_id, user_id):
        self.spotify_track_id = spotify_track_id
        self.tag_id = tag_id
        self.user_id = user_id