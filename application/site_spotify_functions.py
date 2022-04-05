import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
from datetime import datetime
from . import session_cache_path
from flask import redirect

scope = "user-library-read, user-read-playback-state, user-follow-read", "playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


def date_stripper(input_date_string, precision):
    if precision == 'day':
        stripped_date = datetime.strptime(input_date_string, "%Y-%m-%d")
        stripped_date = stripped_date.date()
    elif precision == 'month':
        input_date_string = input_date_string[:7]
        stripped_date = datetime.strptime(input_date_string, "%Y-%m")
        stripped_date = stripped_date.date()
    elif precision == 'year':
        input_date_string = input_date_string [:4]
        stripped_date = datetime.strptime(input_date_string, "%Y")
        stripped_date = stripped_date.date()
    else:
        pprint ("PRECISION DOES NOT MATCH, RETURNING STRING")
        return input_date_string
    return stripped_date


def get_releases_from_artist_ids(list_of_artist_ids, form='dict'):
    """takes list of artist ids
    return list of dicts (form = 'dict)
    or list of id strings 'form='list'"""
    if type(list_of_artist_ids) == str:
        list_of_artist_ids=[list_of_artist_ids]
    album_list = []
    for artist_id in list_of_artist_ids:  # iterate artist ids
        results = sp.artist_albums(artist_id)  # call spotify for artist_album details
        releases = results['items']
        while results['next']:  # check for more pages
            results = sp.next(results)
            releases.extend(results['items'])
        for release in releases:
            album_group = release['album_group']
            album_type = release['album_type']
            album = release['name']
            album_id = release['id']
            spotify_album_url = release['external_urls']['spotify']
            release_date = release['release_date']
            release_date_precision = release['release_date_precision']
            release_date = date_stripper(release_date,
                                         release_date_precision)  # convert date string to datetime obj, insert spurious 1s if precision < day
            album_artist = release['artists'][0]['name']  # get (first) album artist details
            album_artist_id = release['artists'][0]['name']
            release_dict = {
                'artist_id': artist_id,
                'album_artist': album_artist,
                'album_artist_id': album_artist_id,
                'album': album,
                'album_id': album_id,
                'album_group': album_group,
                'album_type': album_type,
                'release_date': release_date,
                'release_date_precision': release_date_precision,
                'spotify_album_url': spotify_album_url
            }
            if form == 'dict':
                album_list.append(release_dict)
            if form == 'list':
                album_list.append(release_dict['album_id'])
    return album_list


def get_tracks_from_artist_ids(list_of_artist_ids, form='dict'):
    """ takes list of artist ids, returns a list of track dicts, or track ids if form=list """

    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)


    if type(list_of_artist_ids) == str:
        list_of_artist_ids = [list_of_artist_ids]

    track_dicts_list = []
    for artist_id in list_of_artist_ids:
        album_list = []
        release_list = get_releases_from_artist_ids(artist_id, 'dict')
        for release in release_list:
            album_id = release['album_id']
            album_list.append(album_id)

        #batch to workaround spotify limit
        for offset in range(0, len(album_list), 20):
            batch = album_list[offset:offset + 20]
            result = spotify.albums(batch)
            albums_batch = result['albums']
            for batched_album in albums_batch:
                album = batched_album['name']
                album_id = batched_album['id']
                album_type = batched_album['album_type']
                for act in batched_album['artists']:
                    album_artist = act['name']
                    album_artist_id = act['id']
                track_id_list = []
                for track in batched_album['tracks']['items']:
                    track_artist = track['artists'][0]['name']
                    track_artist_id = track['artists'][0]['id']
                    title = track['name']
                    spotify_track_url = track['external_urls']['spotify']
                    track_id = track['id']
                    track_id_list.append(track_id)
                    track_dict = {
                        'artist_id': artist_id,
                        'album_artist': album_artist,
                        'album_artist_id': album_artist_id,
                        'album': album,
                        'album_id': album_id,
                        'track_artist': track_artist,
                        'track_artist_id': track_artist_id,
                        'title': title,
                        'track_id': track_id,
                        'album_type': album_type,
                        'spotify_track_url': spotify_track_url
                    }
                    track_dicts_list.append(track_dict)
    if form == 'list':
        return track_id_list
    return track_dicts_list


def make_playlist(playlist_name='python_play'):
    """creates a playlist on user account, returns playlist_id"""
    user = sp.me()['id']
    return sp.user_playlist_create(user=user,name=playlist_name)['id']


def add_to_playlist(playlist_id, track_list):
    sp.playlist_add_items(items=track_list, playlist_id=playlist_id)


def check_playlist_exists(playlist_name):
    """ searches current user's playlists for playlist_name = term returns true if exists"""
    limit = 50
    offset = 0
    current_names = []
    for step in range (0,1000,50):
        current_playlists = sp.current_user_playlists(limit=limit, offset=offset)['items']
        for playlist in current_playlists:
            current_names.append(playlist['name'])
        offset += 50
    if playlist_name in current_names:
        return True

def site_playlist_maker(track_ids, playlist_name):
    if check_playlist_exists(playlist_name):
        print ("PLAYLIST EXISTS")
        pass
    else:
        if len(track_ids) < 10000:
            playlist_id = make_playlist(playlist_name)
            start = 0
            for step in range(start, len(track_ids), 100):
                batch = track_ids[start:start + 100]
                add_to_playlist(playlist_id, batch)
                start += 100
        else:
            count = 1
            begin = 0
            start = 0
            for section in range(begin, len(track_ids), 10000):
                playlist_id = make_playlist(f"{playlist_name} number {count}")
                chunk = track_ids[begin:begin + 10000]
                for step in range(start, len(chunk), 100):
                    batch = track_ids[start:start + 100]
                    add_to_playlist(playlist_id, batch)
                    start += 100
                count += 1
                begin += 10000



#### backups ####

'''

def site_playlist_maker(track_ids, playlist_name):
    if check_playlist_exists(playlist_name):
        print ("PLAYLIST EXISTS")
        pass
    else:
        if len(track_ids)>100:
            
        playlist_id = make_playlist(playlist_name=playlist_name)
        add_to_playlist(playlist_id, track_ids)


'''