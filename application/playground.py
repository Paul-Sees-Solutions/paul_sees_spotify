from spotify_site.spotify_functions import info_getter
from pprint import pprint
selections = ['5dT9JLuBwGNiHJQsY29Qmh']

tracks = info_getter.get_tracks_from_artist_ids(selections)
pprint (tracks)

# releases = info_getter.get_releases_from_artist_ids(selections)
# print (releases)