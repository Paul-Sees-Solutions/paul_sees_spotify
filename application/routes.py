import sys
from pprint import pprint
from . import app, session_cache_path
from .forms import Spot_SearchForm, ArtistTracksForm, ResultsForm, TracklistForm
import uuid
from flask import Flask, request, redirect, session, render_template, url_for, render_template
import os
from wtforms import BooleanField, StringField
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired

import spotipy as sp
from application.site_spotify_functions import get_tracks_from_artist_ids, site_playlist_maker


@app.route('/')
@app.route('/home')
def index():
    if not session.get('uuid'):
        print("not session")
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(scope='user-read-currently-playing playlist-modify-private',
                                          cache_handler=cache_handler,
                                          show_dialog=True)

    if request.args.get("code"):
        print("request.args.get")
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        print("get access token")
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 4. Signed in, display data
    # spotify = sp.Spotify(auth_manager=auth_manager)
    # user_spot = spotify.me()  # get user spotify details
    return render_template('home.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = sp.Spotify(auth_manager=auth_manager)
    form = Spot_SearchForm()
    if request.method == 'POST':
        print('validates')
        search_term = form.search_term.data
        limit = form.how_many.data
        artist = form.artist.data
        album = form.album.data
        track = form.track.data
        release_date = form.release_date.data
        only_new = form.only_new.data
        category = form.category.data
        print (category)
        if 'any' in category:
            category = "artist,album,track,playlist,show,episode"
        else:
            category=','.join(category)
            category.replace(" ","")
            print (type(category),category)
        search_dict = {
            'artist': artist,
            'album': album,
            'track': track,
            'release_date': release_date,
            'only_new': only_new}
        if search_term:
            search_string = search_term
        else:
            search_string = ''
        for thing in search_dict:
            if search_dict[thing]:
                search_string = search_string + " " + thing + ":" + search_dict[thing]

        response = spotify.search(q=search_string, type=category, limit=limit)
        results_dict = {}
        for format in response:
            results = response[format]
            # print (len(results['items']),"RESULTS IN FORMAT",format)
            things = results['items']
            while results['next']:
                # print (len(results['items']),"MORE RESULTS IN FORMAT",format)
                results = spotify.next(results)
                results = results[format]
                things.extend(results['items'])
            print("THERE ARE", len(things), format)
            results_dict.update({format: things})
            # response[format].update(things)
        return results_dict

    print('unvalidated')
    return render_template('search.html', form=form)


##    return spotify.current_user_playlists()

@app.route('/sign_out')
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')


@app.route('/playlists')
def playlists():
    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = sp.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()


@app.route('/currently_playing')
def currently_playing():
    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = sp.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@app.route('/current_user')
def current_user():
    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = sp.Spotify(auth_manager=auth_manager)
    return spotify.current_user()


@app.route('/elaborate', methods=['GET', 'POST'])
def elaborate():
    # prepare spotify
    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = sp.Spotify(auth_manager=auth_manager)

    # get form

    form = ArtistTracksForm()
    if request.method == 'POST':
    # if form.validate():
        artist = form.artist.data
        results = spotify.search(q=artist, type='artist')

        # make a list of dictionaries of results
        elaborate_dict_list = []
        items = results['artists']['items']
        for item in items:
            artist = item['name']
            artist_id = item['id']
            item_dict = {'artist': artist, 'artist_id': artist_id}
            elaborate_dict_list.append(item_dict)
            session.pop('elaborate_dict_list', None)
        session.update({'elaborate_dict_list': elaborate_dict_list})
        return redirect(url_for('return_elaborate'))
    return render_template('elaborate.html', form=form)


@app.route('/return_elaborate', methods=['GET', 'POST'])
def return_elaborate():
    # random_var = request.get
    elaborate_dict_list = session.get('elaborate_dict_list')
    selections = []
    form = ResultsForm()
    # if form.validate():
    if request.method == 'POST':
        own_albums = request.form.get('own_albums')
        own_featured = request.form.get('own_featured')
        own_comp = request.form.get('own_compilations')
        other_own_albums = request.form.get('other_own_albums')
        other_featured = request.form.get('other_featured')
        other_comp = request.form.get('other_compilations')
        selections.extend(request.form.getlist('selections'))
        session.pop('elaborate_selections', None)
        session.update({'elaborate_selections': selections})
        # return "<h1> WEIRD </h1>"
        return redirect(url_for('show_elaborate'))

    return render_template('return_elaborate.html', form=form, elaborate_dict_list=elaborate_dict_list)


@app.route('/show_elaborate', methods=['GET', 'POST'])
def show_elaborate():
    # prepare spotify
    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    form = TracklistForm()
    selections = session.get('elaborate_selections')
    own_albums=request.form.get('own_albums')
    own_featured=request.form.get('own_featured')
    own_comp=request.form.get('own_compilations')
    other_own_albums=request.form.get('other_own_albums')
    other_featured=request.form.get('other_featured')
    other_comp=request.form.get('other_compilations')
    own_tracks=[own_albums,own_featured,own_comp]
    other_tracks=[other_own_albums,other_featured,other_comp]
    if not any(own_tracks):
        own_tracks = False
    elif all(own_tracks):
        own_tracks = True
    elif any(own_tracks):
        own_tracks="some"
    if not any (other_tracks):
        other_tracks=False
    elif all(other_tracks):
        other_tracks=True
    elif any(other_tracks):
        other_tracks="some"

    if request.method== 'POST':
        print("own :", own_tracks, "other", other_tracks)
        return redirect(url_for('made_elaborate'))
    return render_template('show_elaborate.html', form=form)


# TODO: incorporate elaborate options into release search


@app.route('/made_elaborate')
def made_elaborate():
    # playlist_title = session.get('playlist_title')
    return render_template('made_elaborate.html', playlist_title="FAKE TITLE")


@app.route('/all_artist_tracks', methods=['GET', 'POST'])
def all_artist_tracks():
    # prepare spotify
    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = sp.Spotify(auth_manager=auth_manager)

    # get form

    form = ArtistTracksForm()
    if request.method == 'POST':
        artist = form.artist.data
        results = spotify.search(q=artist, type='artist')

        # make a list of dictionaries of results
        all_artist_tracks_dict_list = []
        items = results['artists']['items']
        for item in items:
            artist = item['name']
            artist_id = item['id']
            item_dict = {'artist': artist, 'artist_id': artist_id}
            all_artist_tracks_dict_list.append(item_dict)
        session.update({'all_artist_tracks_dict_list': all_artist_tracks_dict_list})
        return redirect(url_for('return_artists'))
    return render_template('all_artist_tracks.html', form=form)


@app.route('/return_artists', methods=['GET', 'POST'])
def return_artists():
    artist_dict_list = session.get('artist_dict_list')
    selections = []
    form = ResultsForm()
    if request.method == 'POST':
        original = form.original.data
        include = form.include_comp.data
        selections.extend(request.form.getlist('selections'))
        session.pop('selections', None)
        session.update({'selections': selections})
        return redirect(url_for('show_tracklist'))

    return render_template('return_artists.html', form=form, artist_dict_list=artist_dict_list)


@app.route('/show_tracklist', methods=['GET', 'POST'])
def show_tracklist():
    # prepare spotify
    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    selections = session.get('selections')
    tracks = get_tracks_from_artist_ids(selections)
    session.update({'tracklist': tracks})
    form = TracklistForm()
    if request.method == 'POST':
        playlist_title = request.form.get('thetitle')
        print("PLAYLIST TITLE =", playlist_title)
        session.update({'playlist_title': playlist_title})
        track_ids = []
        for track in tracks:
            track_ids.append(track['track_id'])
        site_playlist_maker(track_ids, playlist_title)
        return redirect(url_for('made_playlist'))

    return render_template('show_tracklist.html', form=form, tracks=tracks)


@app.route('/made_playlist')
def made_playlist():
    playlist_title = session.get('playlist_title')
    return render_template('made_playlist.html', playlist_title=playlist_title)


#### backups ####
'''
@app.route('/myresults', methods=['GET', 'POST'])
def myresults():
    artist_dict_list = session.get('artist_dict_list')
    selections = []

    # create html
    output = "<form method='post'>"
    for artist in artist_dict_list:
        output += f"<label> {artist['artist']} </label>" \
                  f"<input type='checkbox' name='hello' value={artist['artist_id']}> <br>"
    output += "<input type='submit'> </form>"

    if request.method == 'POST':
        selections.extend(request.form.getlist('hello'))
        session.update({'selections': selections})

        return redirect(url_for('show_tracklist'))
    return output


@app.route('/show_tracklist', methods=['GET', 'POST'])
def show_tracklist():
    # prepare spotify
    cache_handler = sp.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = sp.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    selections = session.get('selections')
    tracks = get_tracks_from_artist_ids(selections)
    session.update({'tracklist': tracks})
    output = "<h1> The Following Tracks will be in the list, enter a playlist name and click 'confirm' to add playlist to your spotify account </h1>" \
             "<form method='post'>" \
             "<input type='text' name='thetitle'>" \
             "<input type='submit' name='confirm'> "
    for track in tracks:
        output += f"<h3> {track['track_artist']} - {track['title']}</h3>"
    if request.method == 'POST':
        playlist_title = request.form.get('thetitle')
        print("PLAYLIST TITLE =", playlist_title)
        track_ids = []
        for track in tracks:
            pprint (track)
            track_ids.append(track['track_id'])
            print (track_ids)
        site_playlist_maker(track_ids, playlist_title)

    return output

'''
