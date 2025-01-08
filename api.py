from flask_restful import Resource,fields,marshal_with,reqparse
from datetime import datetime
from models import *
from exceptions import *

#<-----USER API----->
#Defining Response Output
user_controls = {
        "user_id" : fields.Integer,
        "username" : fields.String,
        "first_name" : fields.String,
        "last_name" : fields.String,
        "gender" : fields.String,
}

#Defining Request Parser for USER API
user_control_parser = reqparse.RequestParser()
user_control_parser.add_argument('first_name')
user_control_parser.add_argument('last_name')
user_control_parser.add_argument('username')
user_control_parser.add_argument('gender')
user_control_parser.add_argument('password')

#Defining API Class
class UserAPI(Resource):
    @marshal_with(user_controls)
    #HTTP Method -> GET
    def get(self, username):
        #Search for user with username
        user = User.query.filter_by(username = username).first()
        #If user is found
        if user:
            return user
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)
        
    #HTTP Method -> PUT
    def put(self, username):
        #Parse Arguments
        arg = user_control_parser.parse_args()
        firstname = arg.get('first_name', None)
        lastname = arg.get('last_name', None)
        user = User.query.filter_by(username = username).first()

        #If user is found
        if user:
            #If firstname too short raise Exception
            if firstname != 'None' and len(firstname) < 5:
                raise BusninessValidationError(error_message = 'First Name too Short!' ,status_code = 400)
            #Else commit to database
            elif firstname:
                user.first_name = firstname
                if lastname:
                    user.last_name = lastname
                db.session.commit()
                return '',200
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)
    
    #HTTP Method -> DELETE
    def delete(self, username):
        #Search for user based on username
        user = User.query.filter_by(username = username).first()

        #If user is found
        if user:
            db.session.delete(user)
            db.session.commit()
            return "",200
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)
    
    #HTTP Method -> POST
    def post(self):
        #Parse Arguments
        arg = user_control_parser.parse_args()
        firstname = arg.get('first_name', None)
        lastname = arg.get('last_name', None)
        username = arg.get('username', None)
        gender = arg.get('gender', None)
        password = arg.get('password', None)

        #Search for existing users based on username
        user = User.query.filter_by(username=username).first()

        #If firstname error raise Exception
        if firstname =='None' or len(firstname)<=2:
            raise BusninessValidationError(status_code=400,error_message='Firstname Empty or Too short!')
        #If username error raise Exception
        elif username == 'None' or len(username)<=2:
            raise BusninessValidationError(status_code=400,error_message='Username Empty or Too short!')
        #If pre-existing user raise Exception
        elif user:
            raise BusninessValidationError(status_code=400,error_message='Username Unavailable!')
        #If gender invalid raise Exception
        elif not gender or (gender not in ['male','female']):
            raise BusninessValidationError(status_code=400,error_message='Invalid Gender!')
        #If password invalid raise Exception
        elif not password:
            raise BusninessValidationError(status_code=400,error_message='Password cannot be empty!')
        #If password error raise Exception
        elif len(password)<9 or len(password) > 20:
            raise BusninessValidationError(status_code=400,error_message='Password must be between 8 to 20 characters!')
        #Else commit to database
        else:
            user = User(first_name= firstname,last_name=lastname,
            user_name= username,gender=gender,password=password)
            db.session.add(user)
            db.session.commit()
            user_out = User.query.filter_by(username= username).first()
            return user_out
        
#<-----ARTIST API----->
#Defining Response Output
artists_controls = {
        "artist_id": fields.Integer,
        "name": fields.String,
        "albums": fields.Nested({
            "album_id": fields.Integer,
            "album_name": fields.String
        }),
        "songs": fields.Nested({
            "song_id": fields.Integer,
            "title": fields.String
        }),
        "description": fields.String
}

#Defining Request Parser for ARTIST API
artist_control_parser = reqparse.RequestParser()
artist_control_parser.add_argument('name')
artist_control_parser.add_argument('description')

#Defining API Class
class ArtistAPI(Resource):
    @marshal_with(artists_controls)
    #HTTP Method -> GET
    def get(self, artist_id):
        #Seach for artist by artist_id
        artist = Artist.query.filter_by(artist_id = artist_id).first()
        #If artist is found
        if artist:
            return artist
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)

    #HTTP Method -> POST  
    def put(self, artist_id):
        #Parse Arguments
        arg = artist_control_parser.parse_args()
        name = arg.get('name', None)
        description = arg.get('description', None)
        #Search for artist by artist_id
        artist = Artist.query.filter_by(artist_id = artist_id).first()
        #If artist is found
        if artist:
            #If same information entered again raise Exception
            if name == artist.name and description == artist.description:
                raise BusninessValidationError(error_message = 'Same Data Entered Again' , status_code=400)
            
            #Else Commit name to database
            elif name:
                artist.name = name
                #If description also present commit to database
                if description:
                    artist.description = description
                db.session.commit()
                return '',200
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)
    #HTTP Method -> POST
    def post(self):
        #Parse Arguments
        arg = user_control_parser.parse_args()
        name = arg.get('name', None)
        description = arg.get('description', None)

        #Search for artist by artist name
        artist = Artist.query.filter_by(name = name).first()

        #If pre-existing artist raise Exception
        if artist:
            raise BusninessValidationError(error_message='Artist Already Exsists!', status_code=400)
        
        #Else commit to database
        else:
            artist = Artist(name=name, description=description)
            db.session.add(artist)
            db.session.commit()
            artist_out = Artist.query.filter_by(name = name).first()
            return artist_out

#<-----ALBUM API----->
#Defining Response Output
album_controls = {
    "album_id": fields.Integer,
    "album_name": fields.String,
    "artist": fields.Nested({
        "artist_id": fields.Integer,
        "name": fields.String
    }),
    "songs": fields.List(fields.Nested({
        "song_id": fields.Integer,
        "title": fields.String,
        "artist": fields.Nested({
            "artist_id": fields.Integer,
            "name": fields.String
        })
    })),
    "created_at": fields.DateTime,
    "updated_at": fields.DateTime
}

#Defining Request Parser for ALBUM API
album_control_parser = reqparse.RequestParser()
album_control_parser.add_argument('album_name')
album_control_parser.add_argument('artist_name')
album_control_parser.add_argument('song_id')

#Defining API Class
class AlbumAPI(Resource):
    @marshal_with(album_controls)
    #HTTP Method -> GET
    def get(self, album_id):
        #Search for album using album_id
        album = Album.query.filter_by(album_id = album_id).first()
        #If album is found
        if album:
            return album
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)
    
    #HTTP Method -> PUT
    def put(self, album_id):
        #Parse Arguments
        arg = album_control_parser.parse_args()
        album_name = arg.get('album_name', None)
        artist_name = arg.get('artist_name', None)
        song_id = arg.get('song_id', None)

        #Search for albums, artist and songs with album_id, artist_name and song_id
        album = Album.query.filter_by(album_id = album_id).first()
        artist = Artist.query.filter_by(name= artist_name).first()
        song = Song.query.filter_by(song_id = song_id).first()

        #If album exsists
        if album:
            #If same information entered raise Exception
            if album_name and album_name == album.album_name:
                raise BusninessValidationError(error_message='Same Information entered Again!', status_code=400)
            
            #Else proceed
            else:
                album.album_name = album_name
                #Define update time
                album.updated_at = datetime.now()
                #If same information entered again raise Exception
                if artist.artist_id == album.artist_id:
                    raise BusninessValidationError(error_message='Same Information entered Again!', status_code=400)
                #Else commit to database
                else:
                    album.artist_id = artist.artist_id
                    #If song is also present, commit to database
                    if song:
                        song.album_id = album.album_id
                db.session.commit()
                return '',200
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)

    #HTTP Method -> DELETE     
    def delete(self, album_id):
        #Seach for album by album_id
        album = Album.query.filter_by(album_id = album_id).first()

        #If album exists commit to database
        if album:
            db.session.delete(album)
            db.session.commit()
            return '',200
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)
    
    #HTTP Method -> POST
    def post(self):
        #Parse Arguments
        arg = album_control_parser.parse_args()
        album_name = arg.get('album_name', None)
        artist_name = arg.get('artist_name', None)

        #Search for albums and artists by album_name, artist_name respectively
        album = Album.query.filter_by(album_name = album_name).first()
        artist = Artist.query.filter_by(name= artist_name).first()

        #If pre-existing album raise Exception
        if album:
            raise BusninessValidationError(error_message='Album Already Exsists!', status_code=400)
        #Else proceed
        else:
            #If artist is found
            if artist:
                album_artist_id = artist.artist_id
                album = Album(album_name= album_name, artist_id = album_artist_id, created_at = datetime.now(), updated_at= datetime.now())
            #Else commit artist to database
            else:
                artist = Artist(name=artist_name)
                db.session.add(artist)
                db.session.commit()
            #Commit information to database
            db.session.add(album)
            db.session.commit()
            album_out = Album.query.filter_by(album_name).first()
            return album_out

#<-----SONG API----->
#Defining Response Output
song_controls = {
    "song_id": fields.Integer,
    "title": fields.String,
    "artist": fields.Nested({
        "name": fields.String,
    }),
    "album": fields.Nested({
        "album_id": fields.Integer,
        "album_name": fields.String,
        "artist": fields.Nested({
            "artist_id": fields.Integer,
            "name": fields.String
        })
    }),
    "language": fields.String,
    "genre": fields.String,
    "created_at": fields.DateTime
}

#Defining Request Parser for SONG API
song_control_parser = reqparse.RequestParser()
song_control_parser.add_argument('title')
song_control_parser.add_argument('artist_name')
song_control_parser.add_argument('language')
song_control_parser.add_argument('genre')
song_control_parser.add_argument('lyrics')

#Defining API Class
class SongAPI(Resource):
    @marshal_with(song_controls)
    #HTTP Method -> GET
    def get(self, song_id):
        #Search for songs by song_id
        song = Song.query.filter_by(song_id = song_id).first()

        #If song is found
        if song:
            return song
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)
    
    #HTTP Method -> PUT
    def put(self, song_id):
        #Parse Arguments
        arg = song_control_parser.parse_args()
        title = arg.get('title', None)
        artist_name = arg.get('artist_name', None)
        language = arg.get('language', None)
        genre = arg.get('genre', None)
        lyrics = arg.get('lyrics', None)

        #Search for songs, artist by song_id and artist_name
        song = Song.query.filter_by(song_id = song_id).first()
        artist = Artist.query.filter_by(artist_name = artist_name).first()

        #If song is found commit to database
        if song:
            song.title = title
            song.genre = genre
            song.language = language
            song.lyrics = lyrics
            #If artist is found
            if artist:
                song.artist_id = artist.artist_id
            #Else raise Exception
            else:
                raise NotFoundError(status_code=404)
            
            db.session.commit()
            return '', 200
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)

    #HTTP Method -> DELETE            
    def delete(self, song_id):
        #Search for song by song_id
        song = Song.query.filter_by(song_id = song_id).first()

        #If song is found commit to database
        if song:
            db.session.delete(song)
            db.session.commit()
            return '', 200
        #Else raise exception
        else:
            raise NotFoundError(status_code=404)

    #HTTP Method -> POST
    def post(self):
        #Parse Arguments
        arg = song_control_parser.parse_args()
        title = arg.get('title', None)
        artist_name = arg.get('artist_name', None)
        language = arg.get('language', None)
        genre = arg.get('genre', None)
        lyrics = arg.get('lyrics', None)

        #Search for songs, artists by song_title, artist_name
        song = Song.query.filter_by(title= title, language=language).first()
        artist = Artist.query.filter_by(artist_name = artist_name).first()

        #If pre-existing song raise Exception
        if song:
            raise BusninessValidationError(error_message='Song Already Exists!', status_code=400)
        #Else proceed
        else:
            #If artist is found
            if artist:
                song_artist_id = artist.artist_id
            #Else commit to database
            else:
                artist = Artist(name= artist_name)
                db.session.add(artist)
                db.session.commit()
            #Commit song to database
            song = Song(title = title, artist_id= song_artist_id, genre=genre, language= language, lyrics=lyrics, 
                        created_at= datetime.now(), updated_at= datetime.now())
            db.session.add(song)
            db.session.commit()

            song_out = Song.query.filter_by(title= title).first()
            return song_out

#<-----CREATOR API----->
#Defining Response Output   
creator_controls = {
    "user_id": fields.Integer,
    "creator": fields.Nested({
        "username": fields.String,
        "first_name": fields.String
    }),
    "songs": fields.Nested({
        "song_id": fields.Integer,
        "title": fields.String,
        "artist": fields.Nested({
            "artist_id": fields.Integer,
            "name": fields.String
        }),
        "created_at": fields.DateTime
    })
}

#Defining API Class
class CreatorAPI(Resource):
    @marshal_with(creator_controls)
    #HTTP Method -> GET
    def get(self, username):
        #Search for users by username 
        creator = User.query.filter_by(username = username).first()
        #If user is found and the user is a creator
        if creator.is_creator is True:
            #Search for creations, songs using user_id
            creations = Creator.query.filter_by(user_id = creator.user_id).all()
            song_ids = [creation.song_id for creation in creations if creation.song_id is not None]
            songs = Song.query.filter(Song.song_id.in_(song_ids)).all()
            creations_list = [song for song in songs]

            #Create Response dictionary
            creator_dict = {
                "user_id" : creator.user_id,
                "creator" : {
                    "username": creator.username,
                    "first_name": creator.first_name
                },
                "songs" : creations_list
            }
            return creator_dict
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)

    #HTTP Method -> DELETE  
    def delete(self, username):
        #Search for users by username
        creator = User.query.filter_by(username = username).first()

        #If the user is creator commit to database
        if creator.is_creator is True:
            creator.is_creator == False
            db.session.commit()
            return "",200
        #Else raise Exception
        else:
            raise NotFoundError(status_code=404)