# Readme: https://github.com/nikhilgaba001/YoutubeToSpotify/blob/master/README.md

from apiclient.discovery import build
import csv
import spotipy
import spotipy.util as util
import sys

# Number of titles to get from each channel
MAX_RESULT = 10

# Spotify credentials
SPOTIFY_USERNAME = ''
CLIENT_ID = ''
CLIENT_SECRET = ''
SCOPE = 'playlist-modify-private'

# Spotify Playlist which will get the new tracks
YOUTUBE_PLAYLIST_ID = ''

# Youtube credentials
API_KEY = ''

# Add channel usernames from Youtube in this list
CHANNEL_USERNAMES = []

# Add channel IDs from Youtube in this Dictionary like {'channelName' : 'channelID'}
CHANNEL_IDS = {}

# Words to delete from the fetched title name from Youtube
IGNORE = ['(', '[', ' x', ')', ']', '&', 'lyrics', 'lyric',
          'video', '/', ' proximity', ' ft', '.', ' edit', ' feat', ' vs', ',']


# returns youtube client object
def init_youtube_client():
    try:
        print('Initialising Youtube Client....')
        client = build('youtube', 'v3', developerKey=API_KEY)
        print('\nClient initialised!\n')
        return client
    except:
        sys.exit('\nError initialising Youtube Client!\n')


# for channel username
def username_req(client, channel_username):
    req = client.channels().list(part='contentDetails', forUsername=channel_username)
    return req


# for channel id
def id_req(client, channel_id):
    req = client.channels().list(part='contentDetails',
                                 id=channel_id)
    return req


# Takes a request object and youtube client object as input and returns a list of unfiltered titles of a channel
def get_channel_uploads(req, youtube):
    print("\nGetting Channel's uploads...")
    r = req.execute()
    channel_uploads_id = r['items'][-1]['contentDetails']['relatedPlaylists']['uploads']
    req = youtube.playlistItems().list(
        part='snippet', playlistId=channel_uploads_id, maxResults=MAX_RESULT)
    playlist = req.execute()
    videos_list = playlist['items']
    return videos_list


# Takes unfiltered list of channel's titles and returns a filtered list
def filter_titles(videos_list):
    print('Filtering titles...')
    titles = []
    for video in videos_list:
        title = (video['snippet']['title']).lower()
        for ch in IGNORE:
            if ch in title:
                title = title.replace(ch, '')
        artist = (title.rsplit('-')[0]).strip()
        track = (title[len(artist) + 2:]).strip()
        title = (artist + ' ' + track).strip()
        titles.append(title)
    return titles


# Returns a spotify client object
def init_spotify_client():
    try:
        print('Initialising Spotify Client....')
        token = util.prompt_for_user_token(SPOTIFY_USERNAME, SCOPE,
                                           client_id=CLIENT_ID,
                                           client_secret=CLIENT_SECRET,
                                           redirect_uri='http://localhost/')
        spotify_client = spotipy.Spotify(auth=token)
        print('\nClient initialised!\n')
        return spotify_client
    except:
        sys('\nError initialising Spotify Client!\n')


# Takes filtered list of all the titles of channels, search them on spotify, if not found,
# reduces string by a word each time until found or len = 20,
# prints total no. of tracks found, not found and returns a list of all the ids of the tracks found
def search_spotify(spotify_client, titles_list):
    print('\nSearching....\n')
    add_tracks_id_list = []
    not_found = []

    for title in titles_list:
        print(f'Searching Track: {title}')
        with open('searched.csv', mode='a') as searched_file:
            searched_writer = csv.writer(searched_file)
            searched_writer.writerow([title])
        result = spotify_client.search(
            title, limit=1, offset=0, type='track', market=None)
        if result['tracks']['total'] == 0:
            ntitle = title
            while(len(ntitle) >= 25):
                ntitle = ntitle.rsplit(' ', 1)[0]
                print(f'Searching: {ntitle}')
                result = spotify_client.search(
                    ntitle, limit=1, offset=0, type='track', market=None)
                if result['tracks']['total']:
                    result_id = result['tracks']['items'][-1]['id']
                    add_tracks_id_list.append(result_id)
                    print(f'Track found : {ntitle} ')
                    break
            if result['tracks']['total'] == 0:
                print(f'Not found: {title}')
                not_found.append(title)
        else:
            result_id = result['tracks']['items'][-1]['id']
            add_tracks_id_list.append(result_id)
            print(f'Track found : {title}')
    print(f'\nTotal Tracks searched: {len(titles_list)}')
    # tracks_not_found = len(titles_list) - len(add_tracks_id_list)
    if not_found:
        print(f'{len(not_found)} Tracks not found: {not_found}')
    # print(f'Tracks not found: {tracks_not_found} - {not_found[(len(not_found)-tracks_not_found):]}')
    return add_tracks_id_list


# Takes list of track ids to check for new addition, current playlist tracks ids list,
# and adds new tracks to the playlist
def add_tracks_spotify(spotify_client, add_tracks_id_list):
    new = []
    for track in add_tracks_id_list:
        track_ = spotify_client.track(track)
        track_name = track_['name']
        artist = track_['album']['artists'][0]['name']
        name = artist + '-' + track_name
        new.append(name)
        print(f'Adding track: {name}')
    if add_tracks_id_list:
        spotify_client.user_playlist_add_tracks(
            SPOTIFY_USERNAME, YOUTUBE_PLAYLIST_ID, add_tracks_id_list, position=0)
        print(f'\n{len(new)} new tracks added: {new}\n')

    else:
        print('\n***************** No new tracks to add! *****************\n')


# Takes youtube client object as input; for each channel, get channel uploads titles, filters them and returns a list of them
def get_tracks_youtube(youtube):
    final_titles = []
    titles_un = []
    titles_id = []
    SEARCHED_TITLES_LIST = []
    if CHANNEL_USERNAMES:
        for username in CHANNEL_USERNAMES:
            req = username_req(youtube, username)
            videos_list = get_channel_uploads(req, youtube)
            titles = filter_titles(videos_list)
            titles_un += titles
            print(f'{username}, Total: {len(titles)}: {titles}\n')
    if CHANNEL_IDS:
        id_list = list(CHANNEL_IDS.items())
        for item in id_list:
            ch_id = item[1]
            req = id_req(youtube, ch_id)
            videos_list = get_channel_uploads(req, youtube)
            titles = filter_titles(videos_list)
            titles_id += titles
            print(f'{item[0]}, Total: {len(titles)}: {titles}\n')
    total_titles = titles_un + titles_id

    with open('searched.csv') as searched:
        searched_reader = csv.reader(searched, delimiter=',')
        for line in searched_reader:
            SEARCHED_TITLES_LIST.append(line[0])
    for title in total_titles:
        if title not in SEARCHED_TITLES_LIST:
            final_titles.append(title)
    return final_titles


if __name__ == '__main__':
    spotify_client = init_spotify_client()
    youtube = init_youtube_client()
    youtube_titles = get_tracks_youtube(youtube)
    new_tracks = search_spotify(spotify_client, youtube_titles)
    add_tracks_spotify(spotify_client, new_tracks)
