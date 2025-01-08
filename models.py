from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

#<-----User Model----->
class User(db.Model, UserMixin):
    #Define tablename as in database
    __tablename__ = 'users'
    #Define columns as in database
    user_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    first_name = db.Column(db.String(100), nullable = False)
    last_name = db.Column(db.String(100), nullable = True)
    username = db.Column(db.String(), unique = True)
    password = db.Column(db.String(), unique = False)
    gender = db.Column(db.String(), nullable = False)
    is_admin = db.Column(db.Boolean(), default = False)
    is_creator = db.Column(db.Boolean(), default = False)
    #Define relationship between creator table and user table
    #Deleting user account deletes the added songs of the user
    creator = db.relationship('Creator', back_populates = 'users', cascade = 'all, delete-orphan', 
                                primaryjoin = 'Creator.user_id == User.user_id')
    #Define relationship between playlist table and user table
    #Deleting user account deletes associated playlists
    playlist = db.relationship('Playlists', backref='created_by',cascade = 'all, delete-orphan',
                                primaryjoin = 'Playlists.user_id == User.user_id')
    #Define relationship between interaction table and user table
    #Deleting user account deletes all associated interactions
    likes = db.relationship('Interaction', backref = 'likes', cascade = 'all, delete-orphan',
                                primaryjoin = 'Interaction.user_id == User.user_id')

    #Flask login uses id of users table to login a user
    #Since id is defined as user_id, get_id function of Flask login is overrided by this function
    def get_id(self):
        return int(self.user_id)

#<-----Artist Model----->
class Artist(db.Model):
    #Define tablename as in database
    __tablename__ = 'artists'
    #Define columns as in database
    artist_id = db.Column(db.Integer(), autoincrement = True, primary_key = True)
    name = db.Column(db.String(), nullable = False)
    description = db.Column(db.String(500), nullable = True)
    #Define relationship between songs table and artist table
    #Deleting artist, doesn't delete song
    songs = db.relationship('Song', back_populates = 'artist', overlaps='artists_songs,songs')
    #Define relationship between albums table and artist table
    #Deleting artist, doesn't delete album
    album = db.relationship('Album', back_populates = 'artist', overlaps='albums,artists_albums')

#<-----Album Model----->
class Album(db.Model):
    #Define tablename as in database
    __tablename__ = 'albums'
    #Define columns as in database
    album_id = db.Column(db.Integer(), autoincrement = True, primary_key = True)
    artist_id = db.Column(db.Integer(), db.ForeignKey('artists.artist_id'), nullable = False)
    album_name = db.Column(db.String(), nullable = False)
    created_at = db.Column(db.DateTime(timezone = True), server_default = func.now())
    updated_at = db.Column(db.DateTime(timezone = True), server_default = func.now())
    #Define relationship between songs table and album table
    #Deleting album, doesn't delete song
    songs = db.relationship('Song', back_populates = 'album')
    #Define relationship between artist table and album table
    #Deleting album, doesn't delete artist
    artist = db.relationship('Artist', back_populates = 'album')

#<-----Song Model----->
class Song(db.Model):
    #Define tablename as in database
    __tablename__ = 'songs'
    #Define columns as in database
    song_id = db.Column(db.Integer(), autoincrement = True, primary_key = True)
    album_id = db.Column(db.Integer(), db.ForeignKey('albums.album_id'))
    artist_id = db.Column(db.Integer(), db.ForeignKey('artists.artist_id'), nullable = False)
    title = db.Column(db.String(100), nullable = False)
    language = db.Column(db.String(50), nullable = False)
    genre = db.Column(db.String(50), nullable = False)
    lyrics = db.Column(db.String(), nullable = False)
    created_at = db.Column(db.DateTime(timezone = True), server_default = func.now())
    updated_at = db.Column(db.DateTime(timezone = True), server_default = func.now())
    flag = db.Column(db.Boolean(), default = False)
    #Define relationship between songs table and album table
    #Deleting song, doesn't delete album
    album = db.relationship('Album', back_populates = 'songs', overlaps='albums_songs,songs')
    #Define relationship between songs table and artist table
    #Deleting song, doesn't delete artist
    artist = db.relationship('Artist', back_populates = 'songs')

#<-----Playlist Model----->
class Playlists(db.Model):
    #Define tablename as in database
    __table_name__ = 'playlists'
    #Define columns as in database
    playlist_id = db.Column(db.Integer(), autoincrement = True, primary_key = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.user_id'), nullable = False)
    name = db.Column(db.String(), nullable = False)
    created_at = db.Column(db.DateTime(timezone = True), server_default = func.now())
    updated_at = db.Column(db.DateTime(timezone = True), server_default = func.now())
    privacy = db.Column(db.Boolean(), default=False)
    #Define relationship between playlists table and playlists_song table
    #Deleting it, delete playlist_songs data also
    playlist_songs = db.relationship('PlaylistSongs', backref='playlists', cascade='all, delete-orphan',
                                        primaryjoin='Playlists.playlist_id==PlaylistSongs.playlist_id')
    
#<-----Songs in Playlists Model----->
class PlaylistSongs(db.Model):
    #Define tablename as in database
    __tablename__ = 'playlist_song'
    #Define columns as in database
    play_song_id = db.Column(db.Integer(), autoincrement = True, primary_key = True)
    playlist_id = db.Column(db.Integer(), db.ForeignKey('playlists.playlist_id'))
    song_id = db.Column(db.Integer(), db.ForeignKey('songs.song_id'))

#<-----Creator Model----->
class Creator(db.Model):
    #Define tablename as in database
    __tablename__ = 'creators'
    #Define columns as in database
    creator_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.user_id'), primary_key = True)
    song_id = db.Column(db.Integer(), db.ForeignKey('songs.song_id'))
    album_id = db.Column(db.Integer(), db.ForeignKey('albums.album_id'))
    users = db.relationship('User', back_populates = 'creator', cascade = 'all', 
                                primaryjoin = 'Creator.user_id == User.user_id')
    songs = db.relationship('Song', backref='creators_song', cascade='all',
                                primaryjoin='Creator.song_id == Song.song_id')
    album = db.relationship('Album', backref='creators_album', cascade='all',
                                primaryjoin='Creator.album_id == Album.album_id')

#<-----Interactions Model----->
class Interaction(db.Model):
    #Define tablename as in database
    __tablename__ = 'interactions'
    #Define columns as in database
    interaction_id = db.Column(db.Integer(), autoincrement = True, primary_key = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.user_id'))
    song_id = db.Column(db.Integer(), db.ForeignKey('songs.song_id'), nullable = True)
    album_id = db.Column(db.Integer(), db.ForeignKey('albums.album_id'), nullable = True)
    liked = db.Column(db.Boolean(), default = False)