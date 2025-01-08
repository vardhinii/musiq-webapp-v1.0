from flask import Flask, request, flash, url_for
from flask import render_template, redirect
from sqlalchemy import or_, update, and_
from flask_login import LoginManager, login_required, login_user,logout_user, current_user
from flask_restful import Api
from models import *
from api import *
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
from io import BytesIO
import os

#Define Flask App
app = Flask(__name__, template_folder='./templates', static_folder='./static')
#App Secret Key
app.secret_key='thatdatafairy'

#Define database route
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.sqlite3')

#Define directory to save song MP3 files
audio_directory = 'static/audio'
os.makedirs(audio_directory, exist_ok=True)

#Define API imported from api.py
api = Api(app)

#Initialize database imported from models.py
db.init_app(app)
#Create context for Flask App
app.app_context()

#Manage User Login (from flask_login)
login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

#Allow Cross Origins
@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response

#Define App Routes
#<-----ROUTE /----->
@app.route("/", methods=['GET', 'POST'])
def show_index():
    #HTTP Method -> GET
    if request.method == 'GET':
        #Return index page
        return render_template('index.html')

#<-----ROUTE /login----->
@app.route("/login", methods=['GET', 'POST'])
def show_login():
    #HTTP Method -> GET
    if request.method == 'GET':
        #Return login page
        return render_template('login.html')
    
    #HTTP Method -> POST
    elif request.method == 'POST':
        #Fetch values from Login Form
        username = request.form.get('username')
        password = request.form.get('password')

        #Search for user by username (unique to every user)
        user = User.query.filter_by(username= username).first()
        
        #If user is found login
        if user != None and user.password == password:
            login_user(user)

            #Flash Success Message
            flash('Your Login was successful!')
            #Return to main page
            return redirect('/main')
        
        #Else raise Exception in the same page
        else:
            return render_template('login.html', error = 'Invalid Username or Password!')

#<-----ROUTE /signup----->
@app.route("/signup", methods=['GET', 'POST'])
def show_signup():
    #HTTP Method -> GET
    if request.method == 'GET':
        #Return to signup page
        return render_template('signup.html')
    
    #HTTP Method -> POST
    elif request.method == 'POST':
        #Fetch values from SignUp Form
        firstname = request.form.get('f_name')
        lastname = request.form.get('l_name')
        username = request.form.get('username')
        password_1 = request.form.get('password_1')
        password_2 = request.form.get('password_2')
        gender = request.form.get('gender')
        
        #Search for user by username
        user = User.query.filter_by(username = username).first()
        
        #If pre-existing user raise Exception in the same page
        if user:
            return render_template('signup.html', error = 'Username Unavailable!')
        #If invalid gender raise Exception in the same page
        elif gender is None:
            return render_template('signup.html', error = 'Select Gender!')
        #If short firstname raise Exception in the same page
        elif len(firstname) < 5:
            return render_template('signup.html', error = 'Firstname too Short!')
        #If no password raise Exception in the same page
        elif len(password_1) < 9 or len(password_1) > 20:
            return render_template('signup.html', error = 'Password must be between 8 to 20 characters!')
        #If passwords not same raise Exception in the same page
        elif password_1 != password_2:
            return render_template('signup.html', error = 'Passwords do not match!')
        
        #Else commit user to database
        else:
            user = User(first_name=firstname,last_name=lastname,username=username,password=password_1,
             gender = gender)
            
            db.session.add(user)
            db.session.commit()
            #Flash success message
            flash('Account Created Successfully!', category='success')
            #Return to login page
            return redirect("/login")

#<-----ROUTE /admin----->
@app.route("/admin", methods=['GET', 'POST'])
def show_adminlogin():
    #HTTP Method -> GET
    if request.method == 'GET':
        #Return login page for admin
        return render_template('admin_login.html')
    
    #HTTP Method -> POST
    if request.method == 'POST':
        #Fetch values from Admin Login-form
        username = request.form['admin-username']
        password = request.form['admin-password']

        #Search for users by username
        user = User.query.filter_by(username = username).first()

        #If user is admin login user
        if user.is_admin is True and user.password == password:
            login_user(user)
            #Flash success message
            flash('Your Login was successful!')
            #Return to admin dashboard page
            return redirect('/admin/dashboard')
        
        #Else raise Exception in the same page
        else:
            return render_template('admin_login.html', error = 'Invalid Username or Password!')

#<------ROUTE /logout----->
@app.route('/logout')
@login_required #Can be performed only user is logged in
def do_logout():
    #Define user as current_user
    user = current_user
    #Perform Logout
    logout_user()
    #Return login page
    return redirect('/login')

#<-----ROUTE /main----->
@app.route("/main", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def show_main():
    #Define user as current_user
    user = current_user
    #Fetch songs by filtering out flagged songs by admin
    songs = Song.query.filter_by(flag=False).all()
    #Fetch all artists
    artists = Artist.query.all()
    #Fetch interactions for current user by filtering with user_id
    likes = Interaction.query.filter_by(user_id = user.user_id).all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return to songs page
        return render_template('songs.html', title= 'All Songs', user = user, songs = songs, artists = artists, likes = likes)

#<-----ROUTE /main/songs/<int:song_id>----->
@app.route("/main/songs/<int:song_id>", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes song_id as input parameter
def play_songs(song_id):
    #Define user as current_user
    user = current_user
    #Fetch song by filtering with song_id
    song = Song.query.filter_by(song_id = song_id).first()
    #Fetch artist by filtering with song's artist_id
    artist = Artist.query.filter_by(artist_id = song.artist_id).first()
    #Fetch Interaction for that user by filtering with user_id
    likes = Interaction.query.filter_by(user_id = user.user_id).all()

    #Fetch Song Genre by spliting (Song genre is comma seperated string)
    genre = song.genre.split(',')
    #Populate again to string
    genre = [gen.strip() for gen in genre]

    #Search for songs in same genre
    genres = Song.query.filter(or_(*(Song.genre.like(f'%{gen}%') for gen in genre))).all()
    #Search for songs in same language
    langs = Song.query.filter_by(language = song.language).all()

    #Create list of songs in same genre as song but not the same song
    genre_list = [genre for genre in genres if genre != song]
    #Create list of songs in same language as song but not the same song
    lang_list = [lang for lang in langs if lang != song]
    #Update list to remove repetitions from genre_list
    lang_list = [song for song in lang_list if song not in genre_list[0:3]]
    
    #HTTP Method -> GET
    if request.method == 'GET':
        #Return to music player page
        return render_template('music_player.html', song = song, artist= artist, genres=genre_list[0:3], langs = lang_list[0:3] , likes= likes, user=user)

#<-----ROUTE /search----->
@app.route("/search", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def search_bar():
    #Fetch values from searchbar
    search_key = request.form.get('searchbar')
    #Declare emply search_lists
    search_list_songs = []
    search_list_albums = []

    #Fetch all artists
    artists = Artist.query.all()
    #Fetch songs based on entered search key on artist name, song name, song genre, song title, etc.
    search_songs = Song.query.join(Artist).filter(or_(Artist.name.like(f'%{search_key}%'), Song.title.like(f'%{search_key}%'), Song.genre.like(f'%{search_key}%'), Song.language.like(f'%{search_key}%'))).all()
    search_list_songs.extend(search_songs)
    #Fetch albums based on entered search key on artist name, album name.
    search_albums = Album.query.join(Artist).filter(or_(Album.album_name.like(f'%{search_key}%'), Artist.name.like(f'%{search_key}%'))).all()
    search_list_albums.extend(search_albums)

    #Refine search list for songs by removing flagged songs
    final_search = [song for song in search_list_songs if song.flag is False]

    #Retun to search results page
    return render_template('search.html', keyword = search_key, result_song=final_search, result_album=search_list_albums, artists = artists)

#<------ROUTE /main/genre/<string:keyword> -> dance, party, romance----->
@app.route("/main/genre/<string:keyword>", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes keyword as input parameter
def genre_songs(keyword):
    #Define user as current_user
    user = current_user
    
    #Fetch songs based on the key
    songs = Song.query.filter(Song.genre.like(f'%{keyword}%')).all()
    #Fetch all artists
    artists = Artist.query.all()
    #Fetch all interactions for users
    likes = Interaction.query.filter_by(user_id = user.user_id).all()
    #Filter out flagged songs by admin
    songs_list = [song for song in songs if song.flag is False]

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return to songs page
        return render_template('songs.html', title= f'{(keyword).capitalize()} Songs',user = user, songs = songs_list, artists = artists, likes=likes)

#<-----ROUTE /main/albums----->
@app.route("/main/albums", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def show_albums():
    #Define user as current_user
    user = current_user
    #Fetch all albums
    albums = Album.query.all()
    #Fetch all artists
    artists = Artist.query.all()
    #Fetch all interactions based on user_id
    likes = Interaction.query.filter_by(user_id = user.user_id).all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return albums page
        return render_template('albums.html', title = 'Albums', user = user, artists = artists, albums= albums, likes=likes)

#<-----ROUTE /main/playlists----->
@app.route("/main/playlists", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def show_playlists():
    #Define user as current_user
    user = current_user

    #Fetch all public playlists
    playlists = Playlists.query.filter_by(privacy = False).all()
    #Fetch all users
    users = User.query.all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return playlist page
        return render_template('playlists.html', title = 'Playlists', user = user, users = users, playlists = playlists)

#<------ROUTE /main/albums/<int:album_id>/view----->
@app.route("/main/albums/<int:album_id>/view", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def view_albums(album_id):
    #Define user as current_user
    user = current_user
    
    #Fetch current album by album_id
    current_album = Album.query.filter_by(album_id = album_id).first()
    #Fetch all albums
    albums = Album.query.all()
    #Fetch all artists
    artists = Artist.query.all()
    #Fetch songs in the album, that is not flagged by admin
    songs = Song.query.filter_by(album_id = album_id, flag=False)
    #Filter albums by removing the current album
    albums_list = [album for album in albums if album != current_album]

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return to view albums page
        return render_template('view.html', title = 'Album', artists = artists, album= current_album, albums= albums_list[0:7], songs=songs)

#<-----ROUTE /main/playlists/<int:playlist_id>/view----->
@app.route("/main/playlists/<int:playlist_id>/view", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def view_playlists(playlist_id):
    #Define user as current_user
    user = current_user
    
    #Fetch current playlist by playlist_id
    current_playlist = Playlists.query.filter_by(playlist_id = playlist_id).first()
    #Fetch other playlists where privacy is false
    playlists = Playlists.query.filter_by(privacy = False).all()
    #Fetch all users
    users = User.query.all()
    #Fetch songs where songs are in the playlist
    songs = (db.session.query(Song).join(PlaylistSongs, and_(Song.song_id == PlaylistSongs.song_id, PlaylistSongs.playlist_id == playlist_id)).all())
    #Filter playlist by removing current playlist
    playlists_list = [playlist for playlist in playlists if playlist != current_playlist]

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return view playlists page
        return render_template('view_playlist.html', user=user, title = 'Playlist', users=users, playlist= current_playlist, playlists= playlists_list[0:7], songs=songs)

#<-----ROUTE /main/languages/<string:lang>----->
@app.route("/main/languages/<string:lang>", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes lang as input parameter
def show_lang(lang):
    #Capitalize the keyword "lang"
    lang = lang.capitalize()

    #Define user as current_user
    user = current_user

    #Fetch songs by language and not flagged by admin
    songs = Song.query.filter_by(language=lang, flag=False).all()
    #Fetch all artists
    artists = Artist.query.all()
    #Fetch interactions for the user by user_id
    likes = Interaction.query.filter_by(user_id = user.user_id).all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return songs page
        return render_template('songs.html', title=f'{lang} Songs', user=user, songs=songs, likes=likes, artists=artists)

#<-----ROUTE /admin/dashboard----->
@app.route("/admin/dashboard", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def admin_dashboard():
    #Fetch all songs, albums, users
    songs = Song.query.all()
    albums = Album.query.all()
    users = User.query.all()
    #Filter out users and creators from users
    users_list = [user for user in users if user.is_admin is False]
    creator_list = [user for user in users if user.is_creator is True]

    #MatPlotLib to generate Charts
    matplotlib.use('agg')
    #Function to generate charts
    plots = generate_plot()

    #HTTP Method -> GET
    if request.method == 'GET':
        return render_template('app_stats.html', user = current_user, users = users_list, songs =songs, albums = albums, creators = creator_list)

#Function to generate Charts and Plots
def generate_plot():
    #Fetch all songs and users
    songs = Song.query.all()
    users = User.query.all()

    #Filter and create lists of users and creators
    users_list = [user for user in users]
    creator_list = [user for user in users if user.is_creator is True]

    #Filter and create lists of different language songs
    tamil_list = [song for song in songs if song.language == 'Tamil']
    english_list = [song for song in songs if song.language == 'English']
    hindi_list = [song for song in songs if song.language == 'Hindi']
    none_list = [song for song in songs if song.language is None]

    #Piechart 1: Display Users Creators Ratio
    var = np.array([len(creator_list), len(users_list)])
    plt_colors = ["#fc3c44", "#fe5e63"]
    plt_labels = ['Creators', 'Users']
    plt_explode = [0.1, 0]

    fig, ax = plt.subplots()
    ax.pie(var, explode=plt_explode, colors=plt_colors, shadow=True)
    ax.legend(loc='upper right', labels=plt_labels, facecolor='white', framealpha=1)
    fig.set_facecolor('none')
    ax.set_facecolor('none')

    
    output = BytesIO()
    FigureCanvas(fig).print_png(output)
    plt.close(fig)
    output.seek(0)

    output_filename = './static/images/user_creator_piechart.png'
    with open(output_filename, 'wb') as file:
        file.write(output.read())

    #Piechart 2: Display Percentage of different Songs
    var1 = np.array([len(tamil_list), len(english_list), len(hindi_list), len(none_list)])
    plt_colors = ["#fc3c44", "#fe5e63", "#bd3337" , "#fa8b8f" ]
    plt_labels = ['Tamil', 'English', 'Hindi', 'Not Specified']

    fig1, ax1 = plt.subplots()
    ax1.pie(var1, colors=plt_colors, shadow=True)
    ax1.legend(loc='upper right', labels=plt_labels, facecolor='white', framealpha=1)
    fig1.set_facecolor('none')
    ax1.set_facecolor('none')

    output1 = BytesIO()
    FigureCanvas(fig1).print_png(output1)
    plt.close(fig1)
    output1.seek(0)

    output_filename = './static/images/song_languages_piechart.png'
    with open(output_filename, 'wb') as file:
        file.write(output1.read())

#<-----ROUTE /admin/songs----->
@app.route("/admin/songs", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def admin_songs():
    #Define user as current_user
    user = current_user

    #Fetch songs, artists, creators and users
    songs = Song.query.all()
    artists = Artist.query.all()
    creators = Creator.query.all()
    users = User.query.filter_by(is_admin=False).all()
    
    #HTTP Method -> GET
    if request.method == 'GET':
        #Return admin songs page
        return render_template('admin_songs.html', songs = songs, users = users, artists = artists, creators = creators)

#<-----ROUTE /admin/albums----->
@app.route("/admin/albums", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def admin_albums():
    #Define user as current_user
    user = current_user

    #Fetch albums, artists, creators and users
    albums = Album.query.all()
    artists = Artist.query.all()
    creators = Creator.query.all()
    users = User.query.filter_by(is_admin=False).all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return admin albums page
        return render_template('admin_albums.html', albums=albums, users = users, artists = artists, creators = creators)

#<-----ROUTE /admin/songs/add or /creator/songs/add----->
@app.route("/<string:path>/songs/add", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes path as input parameter
def add_songs(path):
    #Define user as current_user
    user = current_user

    #Fetch songs and artists
    songs = Song.query.all()
    artists = Artist.query.all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return add songs page
        return render_template('add_songs.html', songs= songs[0:10], artists = artists, user=user)
    
    #HTTP Method -> POST
    if request.method == 'POST':
        #Fetch values from add songs form
        song_title = request.form.get('song_title')
        artist_id = request.form.get('artist_id')
        genre = request.form.get('genre')
        artist_name = request.form.get('artist_name')
        language = request.form.get('language')
        lyrics = request.form.get('lyrics')
        mp3_file = request.files['audio_file']

        #Fetch song based on song title and artist
        song = Song.query.filter_by(title=song_title, artist_id=artist_id).first()

        #If pre-existing song
        if song:
            #Flash error message
            flash('Song Already Available!')
            #Return same page
            return redirect(request.referrer)
        
        #If language not selected
        elif language is None:
            #Flash error message
            flash('Enter Language!')
            #Return same page
            return redirect(request.referrer)
        
        #Else proceed
        else:
            #If artist name entered
            if artist_name:
                #Commit artist to database
                artist = Artist(name=artist_name)
                db.session.add(artist)
                db.session.commit()

                #Update artist_id with the new artist's artist_id
                artist = Artist.query.filter_by(name=artist_name).first()
                artist_id = artist.artist_id
            
            #Define song to commit to database
            new_song = Song(title=song_title, artist_id = artist_id, genre=genre, language=language, lyrics=lyrics, 
                            created_at=datetime.now(), updated_at=datetime.now())

            db.session.add(new_song)
            db.session.commit()

            #Fetch the same song
            song = Song.query.filter_by(title=song_title).first()

            #If creator
            if user.is_creator is True:
                #Add to creations in database
                creator = Creator(user_id=user.user_id, song_id=song.song_id)
                db.session.add(creator)
                db.session.commit()

            #If MP3 File entered save to /static/audio
            if mp3_file:
                mp3_file.save(os.path.join(audio_directory, f'{song.song_id}.mp3'))
            
            #Flash success message
            flash('Song Added Successfully!')

            #If creator return to creator dashboard
            if user.is_creator is True:
                return redirect(url_for('creator_home', username=user.username))
            
            #Else return to admin/songs page
            elif user.is_admin is True:
                return redirect("/admin/songs")

#<-----ROUTE /songs/<int:song_id>/update----->
@app.route("/songs/<int:song_id>/update", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes song_id as input parameter
def update_songs(song_id):
    #Define user as current_user
    user = current_user

    #Fetch song by song_id and artists
    song = Song.query.filter_by(song_id=song_id).first()
    artists = Artist.query.all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return update songs page
        return render_template('update_songs.html', song=song, artists=artists, user=user)
    
    #HTTP Method -> POST
    if request.method == 'POST':
        #Fetch values from update songs form
        song_title = request.form.get('song_title')
        artist_id = request.form.get('artist_id')
        genre = request.form.get('genre')
        language = request.form.get('language')
        lyrics = request.form.get('lyrics')

        #Update and commit to database
        db.session.execute(update(Song).where(Song.song_id == song_id).values(title=song_title, artist_id =artist_id, genre=genre,
                                                                               language=language, lyrics=lyrics, updated_at=datetime.now()))
        db.session.commit()
        #Flash success message
        flash('Song Updated Successfully!')

        #If admin return to songs page
        if user.is_admin is True:
            return redirect('/admin/songs')
        
        #If creator return to home page
        elif user.is_creator is True:
            return redirect(url_for("creator_home"), username=user.username)

#<-----ROUTE /songs/<int:song_id>/delete----->
@app.route("/songs/<int:song_id>/delete", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes song_id as input parameter
def delete_songs(song_id):
    #Fetch song by song_id
    songs = Song.query.filter_by(song_id=song_id).first()

    #Delete song from database
    db.session.delete(songs)
    db.session.commit()

    #Flash success message
    flash('Song deleted Successfully!')
    #Return same page
    return redirect(request.referrer)

@app.route("/<string:path>/albums/add", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes path as input parameter
def add_albums(path):
    #Define user as current_user
    user = current_user

    #Fetch albums and artists
    albums = Album.query.all()
    artists = Artist.query.all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return add albums page
        return render_template('add_albums.html', albums=albums[0:5], artists = artists, user=user)
    
    #HTTP Method -> POST
    if request.method == 'POST':
        #Fetch values from add albums form
        album_name = request.form.get('album_name')
        artist_id = request.form.get('artist_id')

        #Search albums based on input values
        album = Album.query.filter_by(album_name = album_name, artist_id = artist_id).first()

        #If pre-existing album
        if album:
            flash('Album already Exists!')
            return redirect(request.referrer)
        
        #Else commit album to database
        else:
            album = Album(album_name=album_name, artist_id=artist_id, created_at=datetime.now(), updated_at=datetime.now())
            db.session.add(album)
            db.session.commit()

            #Flash success message
            flash('Album added Successfully!')

            #If creator
            if user.is_creator is True:
                #Commit creation to database
                creator = Creator(user_id=user.user_id, album_id=album.album_id)
                db.session.add(creator)
                db.session.commit()
                #Return creator dashboard
                return redirect(url_for('creator_home', username=user.username))
            
            #If admin return admin albums page
            elif user.is_admin is True:
                return redirect("/admin/albums")

#<-----ROUTE /albums/<int:album_id>/update----->
@app.route("/albums/<int:album_id>/update", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes album_id as input parameter
def update_albums(album_id):
    #Define user as current_user
    user = current_user
    #Filter album based on album_id and fetch all albums and artists
    album = Album.query.filter_by(album_id=album_id).first()
    artists = Artist.query.all()
    songs = Song.query.all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return page update albums
        return render_template('update_albums.html', album=album, artists=artists, songs=songs, user=user)
    
    #HTTP Method -> POST
    if request.method == 'POST':
        #Fetch values from update album form
        album_name = request.form.get('album_name')
        artist_id = request.form.get('artist_id')
        song_id = request.form.get('song_id')

        #Fetch song by song_id
        song = Song.query.filter_by(song_id=song_id).first()

        #If song already in album
        if song and song.album_id == album_id:
            #Flash error message
            flash('Song already in the Album!')
            #Return same page
            return redirect(request.referrer)
        
        #Else commit to database and update details
        else:
            db.session.execute(update(Album).where(Album.album_id == album_id).values(album_name=album_name,
                                                                                       artist_id=artist_id, updated_at=datetime.now()))
            db.session.execute(update(Song).where(Song.song_id == song_id).values(album_id = album_id, updated_at=datetime.now()))
            db.session.commit()

            #Flash success message
            flash('Album Updated Successfully!')

            #If admin redirect to admin albums page
            if user.is_admin is True:
                return redirect('/admin/albums')

            #If creator redirect to creator home
            elif user.is_creator is True:
                return redirect(url_for("creator_home", username=user.username))

#<-----ROUTE /albums/<int:album_id>/delete----->
@app.route("/albums/<int:album_id>/delete", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes album_id as input parameter
def delete_albums(album_id):

    #Filter album by album_id
    album = Album.query.filter_by(album_id=album_id).first()
    
    #Update database and remove album_id from song
    db.session.execute(update(Song).where(Song.album_id == album_id).values(album_id = None))
    db.session.delete(album)
    db.session.commit()

    #Flash success message
    flash('Album deleted Successfully!')
    #Return to same page
    return redirect(request.referrer)

#<-----ROUTE /admin/users----->
@app.route("/admin/users", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
def view_users():
    #Fetch all users except admin
    users = User.query.filter_by(is_admin=False).all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return to user information page
        return render_template('users.html', users=users)

#<-----ROUTE /user/<string:username>----->
@app.route("/user/<string:username>", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes username as input parameter
def user_home(username):
    #Define user as current_user
    user = current_user

    #Fetch albums, playlists, and songs by the user
    playlists = Playlists.query.filter_by(user_id = user.user_id).all()
    likes = Interaction.query.filter_by(user_id = user.user_id).all()
    songs = Song.query.filter_by(song_id = Interaction.song_id, flag=False).all()
    artists1 = Artist.query.filter_by(artist_id = Song.artist_id).all()
    albums = Album.query.filter_by(album_id = Interaction.album_id).all()
    artists2 = Artist.query.filter_by(artist_id = Album.artist_id).all()

    #Filter likes by albums and songs
    likes_list1 = [like for like in likes if like.album_id is None]
    likes_list2 = [like for like in likes if like.song_id is None]
    
    #HTTP Method -> GET
    if request.method == 'GET':
        #Return user dashboard page
        return render_template('user_dashboard.html', user= user, playlists=playlists, likes1 = likes_list1,
                                likes2 = likes_list2, songs = songs, artists1 = artists1, artists2 = artists2, albums=albums)

#<-----ROUTE /user/<string:username>/playlists/add----->
@app.route("/user/<string:username>/playlists/add", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes username as input parameter
def add_playlists(username):
    #Define user as current_user
    user = current_user

    #Fetch songs and playlists 
    songs = Song.query.filter_by(flag=False).all()
    playlists = Playlists.query.all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return add playlists page
        return render_template('add_playlists.html', user = user, songs=songs, playlists=playlists[0:5])
    
    #HTTP Method -> POST
    if request.method == 'POST':
        #Fetch values from add playlist form
        playlist_name = request.form.get('playlist_name')
        privacy = request.form.get('privacy')

        #Search for playlist with same name, and user_id
        playlist = Playlists.query.filter_by(name=playlist_name, user_id=user.user_id).first()

        #If playlist
        if playlist:
            #Flash error message
            flash('Playlist Name already Exists!')
            #Return to same page
            return redirect(request.referrer)
            
        #Else
        else:
            #Set Privacy
            if privacy == 'public':
                privacy = False

            else:
                privacy = True
            
            #Commit playlist to database
            playlist = Playlists(name=playlist_name, user_id=user.user_id, privacy=privacy, created_at=datetime.now()
                                 , updated_at=datetime.now())
            
            db.session.add(playlist)
            db.session.commit()
            #Flash success message
            flash('Playlist created successfully!')
            #Return to user dashboard
            return redirect(url_for('user_home', username=user.username))

#<-----ROUTE /user/playlists/<int:playlist_id>/update----->
@app.route("/user/playlists/<int:playlist_id>/update", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes playlist_id as input parameter
def update_playlists(playlist_id):
    #Define user as current_user
    user = current_user

    #Fetch playlist by playlist_id
    playlist = Playlists.query.filter_by(playlist_id=playlist_id, user_id=user.user_id).first()

    #Fetch songs to add to playlist
    songs = Song.query.filter_by(flag=False).all()

    #HTTP Method -> GET
    if request.method == 'GET':
        #Return update playlists page
        return render_template('update_playlists.html', playlist=playlist, songs=songs)
    
    #HTTP Method -> POST
    if request.method == 'POST':
        #Fetch values from update playlist form
        playlist_id = playlist_id
        playlist_name = request.form.get('playlist_name')
        privacy = request.form.get('privacy')
        song_id = request.form.get('song_id')

        #Set Privacy
        if privacy == 'public':
            privacy = False

        else:
            privacy = True

        #Commit changes to database
        db.session.execute(update(Playlists).where(Playlists.playlist_id == playlist_id).values(name=playlist_name, 
                                                                                                privacy=privacy, updated_at=datetime.now()))
        playlist_song = PlaylistSongs(playlist_id=playlist_id, song_id=song_id)
        db.session.add(playlist_song)
        db.session.commit()

        #Flash success message
        flash('Playlist Updated Successfully!')
        #Return to user dashboard
        return redirect(url_for('user_home', username=user.username))

#<-----ROUTE /user/playlists/<int:playlist_id>/delete----->
@app.route("/user/playlists/<int:playlist_id>/delete", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes playlist_id as input parameter
def delete_playlists(playlist_id):
    #Define user as current_user
    user = current_user

    #Fetch playlists and playlist_songs
    playlist = Playlists.query.filter_by(playlist_id= playlist_id).first()
    playlist_songs = PlaylistSongs.query.filter_by(playlist_id=playlist_id).all()

    db.session.delete(playlist)
    db.session.delete(playlist_songs)
    db.session.commit()

    #Flash success message
    flash('Playlist deleted Successfully!')
    #Return to same page
    return redirect(request.referrer)

#<-----ROUTE /creator/<string:username>----->
@app.route("/creator/<string:username>", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes username as input parameter
def creator_home(username):
    #Define user as current_user
    user = current_user

    #HTTP Method -> GET
    if request.method == 'GET':
        #If creator
        if user.is_creator:
            #Fetch songs, albums and artists by creator
            creators =  Creator.query.filter_by(user_id = user.user_id).all()
            songs = Song.query.all()
            artists = Artist.query.all()
            albums = Album.query.all()
            creators_list1 = [create for create in creators if create.album_id is None]
            creators_list2 = [create for create in creators if create.song_id is None]

            #Return creator dashboard page
            return render_template('creator.html', user=user, songs=songs, creators1 = creators_list1, creators2 = creators_list2, albums=albums, artists = artists)
        
        #Else create creator account
        else:
            db.session.execute(update(User).where(User.user_id == user.user_id).values(is_creator=True))
            db.session.commit()

            #Flash success message
            flash('Creator account created successfully!')
            #Return to user dashboard
            return redirect(url_for('user_home', username=user.username))

#<-----ROUTE /creator/<string:username>/delete----->
@app.route("/creator/<string:username>/delete", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes username as input parameter
def creator_delete(username):
    #Define user as current_user
    user = current_user

    #If creator delete creator account
    if user.is_creator:
        db.session.execute(update(User).where(User.user_id == user.user_id).values(is_creator=False))
        db.session.commit()

        #Flash success message
        flash('Creator account deleted successfully!')
        #Return user dashboard
        return redirect(url_for('user_home', username=user.username))

#<-----ROUTE /user/<string:username>/delete----->
@app.route("/user/<string:username>/delete", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes username as input parameter
def user_delete(username):
    #Define user as current_user
    user = current_user
    
    #Delete user account
    db.session.delete(user)
    db.session.commit()

    #Flash success message
    flash('Account deleted successfully!')
    #Return login page
    return redirect("/login")

#<-----ROUTE /main/songs/<int:song_id>/like----->
@app.route("/main/songs/<int:song_id>/like", methods=['GET','POST'])
@login_required #Can be performed only user is logged in
#Function takes song_id as input parameter
def like_songs(song_id):
    #Define user as current_user
    user = current_user

    #Add interaction and commit to database
    interaction = Interaction(user_id = user.user_id, song_id= song_id, liked=True)
    db.session.add(interaction)
    db.session.commit()

    #Flash success message
    flash('Song Added to Liked Songs!')
    #Return same page
    return redirect(request.referrer)

#<-----ROUTE /main/songs/<int:song_id>/dislike----->
@app.route("/main/songs/<int:song_id>/dislike", methods=['GET','POST'])
@login_required #Can be performed only user is logged in
#Function takes song_id as input parameter
def dislike_songs(song_id):
    #Define user as current_user
    user = current_user
    #Fetch interaction by song_id
    interaction = Interaction.query.filter_by(song_id = song_id, user_id=user.user_id).first()

    #If interaction delete it
    if interaction:
        db.session.delete(interaction)
        db.session.commit()

    #Flash success message
    flash('Song removed from Liked Songs!')
    #Return same page
    return redirect(request.referrer)

#<-----ROUTE /main/albums/<int:album_id>/like----->
@app.route("/main/albums/<int:album_id>/like", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes album_id as input parameter
def like_album(album_id):
    #Define user as current_user
    user = current_user

    #Define Interaction and commit to database
    interaction = Interaction(user_id = user.user_id, album_id= album_id, liked=True)
    db.session.add(interaction)
    db.session.commit()

    #Flash success message
    flash('Album Added to Liked Albums!')
    #Redirct same page
    return redirect(request.referrer)

#<-----ROUTE /main/albums/<int:album_id>/dislike----->
@app.route("/main/albums/<int:album_id>/dislike", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes album_id as input parameter
def dislike_album(album_id):
    #Define user as current_user
    user = current_user

    #Fetch interaction by album_id and user_id
    interaction = Interaction.query.filter_by(album_id = album_id, user_id=user.user_id).first()

    #If interaction delete
    if interaction:
        db.session.delete(interaction)
        db.session.commit()

    #Flash success message
    flash('Album removed from Liked Albums!')
    #Return same page
    return redirect(request.referrer)

#<-----ROUTE /admin/songs/<int:song_id>/flag----->
@app.route("/admin/songs/<int:song_id>/flag", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes song_id as input parameter
def flag_songs(song_id):
    user = current_user

    #Fetch song by song_id
    song = Song.query.filter_by(song_id = song_id).first()

    #If not flagged, flag and commit to database
    if song.flag is False:
        db.session.execute(update(Song).where(Song.song_id == song_id).values(flag=True))
        db.session.commit()
    
    #Flash success message
    flash('Song added to Flagged Songs!')
    #Return same page
    return redirect(request.referrer)

#<-----ROUTE /admin/songs/<int:song_id>/unflag----->
@app.route("/admin/songs/<int:song_id>/unflag", methods=['GET', 'POST'])
@login_required #Can be performed only user is logged in
#Function takes song_id as input parameter
def unflag_songs(song_id):
    #Define user as current_user
    user = current_user

    #Fetch song by song_id
    song = Song.query.filter_by(song_id = song_id).first()

    #If the song is flagged, unflag
    if song.flag is True:
        db.session.execute(update(Song).where(Song.song_id == song_id).values(flag=False))
        db.session.commit()

    #Flash success message
    flash('Song removed from Flagged Songs!')
    return redirect(request.referrer)

#API Resources added with defined path
api.add_resource(UserAPI,"/api/users","/api/users/<string:username>")
api.add_resource(ArtistAPI, "/api/artists", "/api/artists/<int:artist_id>")
api.add_resource(AlbumAPI, "/api/albums", "/api/albums/<int:album_id>")
api.add_resource(SongAPI, "/api/songs", "/api/songs/<int:song_id>")
api.add_resource(CreatorAPI, "/api/creators", "/api/creators/<string:username>")

#Run Application
if __name__ == '__main__':
    app.debug = True
    app.host = '127.0.0.1'
    app.port = 5000
    app.run()