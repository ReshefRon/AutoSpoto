######################
### Import Modules ###
######################

import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect
import pandas as pd
import pycountry

###################
### Credentials ###
###################

CLIENT_ID = "5cb4b2ad22384d50895fec608a8402ce"
CLIENT_SECRET = "0b24f5222dea45b390fe8432569f22a0"

#################
### CONSTANTS ###
#################

KM_DICTIONARY = {
"450":130,
"428":135,
"409":140,
"391":145,
"373":150,
"354":155,
"337":160,
"317":165,
"298":170,
"279":175,
"261":180,
"242":185,
"224":190,
"205":195,
"187":200
}

###################################################################################
### This function purpose is to validate the numeric input from the user.       ###
### We check that the input is from type int and not positive                   ###
### The function keeps looping until the user enter valid input.                ###
###################################################################################


def check_int_input_is_valid(input_string, default_format, units=None):
    while True:
        try:
            if (default_format == True) and (units == None):
                input_value = int(input(f"Enter your {input_string}: "))
            elif (default_format == True) and (units != None):
                input_value = int(input(f"Enter your {input_string} {units}: "))
            elif default_format != True:
                input_value = eval(default_format)

            if input_value < 0:
                print(f"{input_string} must be positive")
            else:
                return input_value
        except ValueError:
            print(f"Invalid input. {input_string} must be a number")


'''
###########################################################################################################################
### When openning  the program, the user should enter                                                                   ###
### 1. USER_NAME - Need to check if User Name exists (addition)                                                         ###
### 2. Age                                                                                                              ###
### 3. Height & Weight - There is a function 'calculae_BMI' for future use                                              ###
### 4. Distance and average Time - possible to add more than one                                                        ###
### We use 'check_int_input_is_valid' to do validation on the numeric parameters (all of them except of the USER NAME)  ###
###########################################################################################################################
'''
def get_user_info():
    USER_NAME = input("Enter User Name: ")

    AGE = check_int_input_is_valid("Age", True, None)
    WEIGHT = check_int_input_is_valid("Weight", True, "(KG)")
    HEIGHT = check_int_input_is_valid("HEIGHT", True, "(CM)")

    DISTANCE_TIME = []
    while True:
        DIST_FORMAT = 'int(input("Enter your common running Distance(KM): "))'
        DISTANCE = check_int_input_is_valid("Distance", DIST_FORMAT, None)

        while True:
            TIME = input("Enter your average result for this distance(MM:SS): ")
            if len(TIME) != 5:
                print("Invalid input! Try again...")
            elif TIME[2] != ":":
                print("Invalid input! Try again...")
            else:
                try:
                    MM = int(TIME[:2])
                    SS = int(TIME[3:])
                    if (MM < 0) or (SS < 0):
                        print("Time must be positive!")
                    elif SS > 59:
                        print("Wrong time format!")
                    else:
                        break
                except ValueError:
                    print("Invalid input! Wrong values... ")

        while True:
            ANOTHER_LOOP = input("Do you want to add another running distance? (Y/N) ")
            if (ANOTHER_LOOP != "N") and (ANOTHER_LOOP != "Y"):
                print("Invalid input. Please Try again...")
            else:
                break
        DISTANCE_TIME.append((DISTANCE, TIME))
        if ANOTHER_LOOP == "Y":
            continue
        elif ANOTHER_LOOP == "N":
            return (USER_NAME,AGE,WEIGHT,HEIGHT,DISTANCE_TIME)
'''
######################
### For future use ###
######################
'''
def calculae_BMI(height, weight):
    return float(weight/(height*height))

'''
###########################################################################################################################
### The function got a list of tuples as an argument. Each tuple includes the Distance and the Average Time.            ###
### 1. Convert the Time format to seconds.                                                                              ###
### 2. Calculate the pace (secs/km) by dividing the values from step 1 by the Distance value from the tuple.            ###
### 3. Then I use the for loop to search for the closest pace in the KM_DICTIONARY (see above).                         ###
### 4. Add the pace (this is the value in the dictionary) to 'paces'.                                                   ###
### 5. return 'paces'                                                                                                   ###
###########################################################################################################################
'''
def calculate_pace(lst):
    paces = []
    for i in lst:
        time_in_seconds = int(i[1][:2]) * 60 + int(i[1][3:])
        seconds_per_km = float(time_in_seconds / i[0])
        matched_key, matched_value = 100, 0
        for key_pace in [int(key) for key in KM_DICTIONARY.keys()]:
            diff = abs(key_pace-seconds_per_km)
            if diff < matched_key:
                matched_key = diff
                matched_value = key_pace
        paces.append(KM_DICTIONARY[str(matched_value)])
    return paces

'''
###################################################################################################################
### This function return a list of tuples (track_name,track_id,track_duration(sec))                             ###
### from the liked songs of the current user which their tempo is in the around 5bpm from the user average pace ###
###################################################################################################################
'''
def liked_songs(sp,pace):
    offset = 0
    total_saved_tracks = 0
    selected_tracks = []

    target_tempo = pace
    tempo_range = (target_tempo - 5, target_tempo + 5)

    while True:
        if ((offset % 50) != 0):
            break
        liked_tracks = sp.current_user_saved_tracks(limit=50, offset=offset)
        total_saved_tracks += len(liked_tracks['items'])
        offset += len(liked_tracks['items'])

        playlist_tracks_names = []
        playlist_tracks_ids = []
        playlist_tracks_durations = []

        for item in liked_tracks['items']:
            playlist_tracks_names.append (item['track']['name'])
            playlist_tracks_ids.append(item['track']['id'])
            playlist_tracks_durations.append(item['track']['duration_ms'])


        playlist_tracks_durations = [x/1000 for x in playlist_tracks_durations]
        audio_features = sp.audio_features(playlist_tracks_ids)
        playlist_tracks_tempo = [track['tempo'] for track in audio_features]

        tracks_df = pd.DataFrame()
        tracks_df['name'] = playlist_tracks_names
        tracks_df['id'] = playlist_tracks_ids
        tracks_df['time(sec)'] = playlist_tracks_durations
        tracks_df['tempo(bpm)'] = playlist_tracks_tempo

        for index, row in tracks_df.iterrows():
            if row['tempo(bpm)'] >= tempo_range[0] and row['tempo(bpm)'] <= tempo_range[1]:
                selected_tracks.append((row['name'], row['id'], row['time(sec)']))

    return selected_tracks
'''
###############################################################################################
### This function return the playlist id of the top 50 songs of the current user's country  ###
################################################################################################
'''

def find_playlist_id_by_country(sp):
    user_country_code = sp.current_user()['country']
    country_name = pycountry.countries.get(alpha_2=user_country_code).name
    search_results = sp.search(q=f'Top 50 {country_name}', type='playlist', limit=1)
    if search_results['playlists']['items']:
        top_playlist_id = search_results['playlists']['items'][0]['id']
    return top_playlist_id

'''
###########################################################################################################################################
### This function return a list of tuples (track_name,track_id,track_duration(sec))                                                     ###
### from the top 50 songs global and top 50 songs of the current users' country,and the tempo i around 5bpm from the user average pace  ###
###########################################################################################################################################
'''

def top_songs(sp,pace):
    selected_tracks = []

    target_tempo = pace
    tempo_range = (target_tempo - 5, target_tempo + 5)

    TOP_LOCAL_ID = find_playlist_id_by_country(sp)
    TOP_GLOBAL_ID = '37i9dQZEVXbNG2KDcFcKOF'

    top_songs = sp.playlist_items(playlist_id=TOP_GLOBAL_ID, limit=50)['items']
    top_songs.extend(sp.playlist_items(playlist_id=TOP_LOCAL_ID, limit=50)['items'])

    playlist_tracks_names = []
    playlist_tracks_ids = []
    playlist_tracks_durations = []

    for item in top_songs:
        playlist_tracks_names.append(item['track']['name'])
        playlist_tracks_ids.append(item['track']['id'])
        playlist_tracks_durations.append(item['track']['duration_ms'])

    playlist_tracks_durations = [x / 1000 for x in playlist_tracks_durations]
    audio_features = sp.audio_features(playlist_tracks_ids)
    playlist_tracks_tempo = [track['tempo'] for track in audio_features]

    tracks_df = pd.DataFrame()
    tracks_df['name'] = playlist_tracks_names
    tracks_df['id'] = playlist_tracks_ids
    tracks_df['time(sec)'] = playlist_tracks_durations
    tracks_df['tempo(bpm)'] = playlist_tracks_tempo

    for index, row in tracks_df.iterrows():
        if row['tempo(bpm)'] >= tempo_range[0] and row['tempo(bpm)'] <= tempo_range[1]:
            selected_tracks.append((row['name'], row['id'], row['time(sec)'], row['tempo(bpm)']))

    return selected_tracks

'''
###############################################################################
### This function returns a list of playlists (tuples of name&id):          ###
### First, the "Made for you" running mixes.                                ###
### Second, the specific "XXX BPM Mix" according to the user average pace.  ###
###############################################################################
'''
def get_all_playlists(sp,tempo):
    playlists = []

    results = sp.search(q='Running Mix', type='playlist',limit=20)


    for playlist in results['playlists']['items']:
        creator = playlist['owner']['display_name']
        if creator == 'Spotify':
            playlists.append((playlist['name'],playlist['id']))

    results = sp.search(q=f'{tempo} BPM Mix,', type='playlist', limit=1)
    for playlist in results['playlists']['items']:
        playlists.append((playlist['name'],playlist['id']))
    return playlists

'''
##################################################################################################
### This function returns a list of tracks (tuples of name-id-duration):                       ###
### We extract only the tracks which their tempo is 5 bpm around the current user average bpm  ###
##################################################################################################
'''

def get_playlist_tracks(sp,pace, playlist_id):
    selected_tracks = []

    target_tempo = pace
    tempo_range = (target_tempo - 5, target_tempo + 5)

    results = sp.playlist_tracks(playlist_id=playlist_id, limit=50)

    playlist_tracks_names = []
    playlist_tracks_ids = []
    playlist_tracks_durations = []

    for item in results['items']:
        playlist_tracks_names.append(item['track']['name'])
        playlist_tracks_ids.append(item['track']['id'])
        playlist_tracks_durations.append(item['track']['duration_ms'])

    playlist_tracks_durations = [x / 1000 for x in playlist_tracks_durations]
    audio_features = sp.audio_features(playlist_tracks_ids)
    playlist_tracks_tempo = [track['tempo'] for track in audio_features]

    tracks_df = pd.DataFrame()
    tracks_df['name'] = playlist_tracks_names
    tracks_df['id'] = playlist_tracks_ids
    tracks_df['time(sec)'] = playlist_tracks_durations
    tracks_df['tempo(bpm)'] = playlist_tracks_tempo

    for index, row in tracks_df.iterrows():
        if row['tempo(bpm)'] >= tempo_range[0] and row['tempo(bpm)'] <= tempo_range[1]:
            selected_tracks.append((row['name'], row['id'], row['time(sec)'], row['tempo(bpm)']))

    return selected_tracks

'''
###############################################################################################
### Iterate all the playlists we found in get_all_playlists and then extract their tracks   ###
### using get_playlist_tracks.                                                              ###
###############################################################################################
'''

def running_made_for_you(sp,pace):
    all_playlists = get_all_playlists(sp, pace)
    selected_tracks = []
    for playlist in all_playlists:
        selected_tracks.extend(get_playlist_tracks(sp, pace, playlist[1]))
    return selected_tracks


'''
###############################################################################################################################
### After we use all these previous functions, I use the list of relevant tracks to create the new Playlists in the user's  ###
### spotify account                                                                                                         ###
###############################################################################################################################
'''

def create_new_playlist(sp,username,pace,dist,tracks_ids_list):
    current_user_id = sp.current_user()['id']
    new_playlist = sp.user_playlist_create(user=current_user_id, name=f"{username}'s {pace} BPM playlist for {dist} KM", public=False)
    sp.playlist_add_items(playlist_id=new_playlist['id'], items=tracks_ids_list)

'''
###############################################################################################
### Authorization - Get a token and then Create spotify_oauth for using the Spotify API.    ###                                                                   
###  Create Flask environment -                                                             ###                                                                                     
### Credit: "Spotify OAuth: Automating Discover Weekly Playlist - Full Tutorial             ###
### ("https://www.youtube.com/watch?v=mBycigbJQzA&list=FLHqPxZfQKFwoGjPAAChjl9w")           ###                         
###############################################################################################
'''

def create_app():
    app = Flask(__name__)

    app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
    app.secret_key = 'sdjkbhf4278r02jfnvcf289-1fm49-'
    TOKEN_INFO = 'token_info'


    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET

    @app.route('/')
    def login():
        auth_url = create_spotify_oauth().get_authorize_url()
        return redirect(auth_url)

    @app.route('/redirect')
    def redirect_page():
        session.clear()
        code = request.args.get('code')
        token_info = create_spotify_oauth().get_access_token(code)
        session[TOKEN_INFO] = token_info
        return redirect(url_for('save_playlist',_external=True))

    @app.route('/savePlaylist')
    def save_playlist():
        try:
            token_info = get_token()
        except:
            print("User not logged in")
            return redirect('/')

        sp = spotipy.Spotify(auth=token_info['access_token'])
        USER_NAME, AGE, WEIGHT, HEIGHT, DISTANCE_TIME = get_user_info()
        list_of_paces = calculate_pace(DISTANCE_TIME)
        for i in range(len(list_of_paces)):
            tracks_for_playlist = []
            tracks_for_playlist.extend(liked_songs(sp, list_of_paces[i]))
            tracks_for_playlist.extend(top_songs(sp, list_of_paces[i]))
            tracks_for_playlist.extend(running_made_for_you(sp, list_of_paces[i]))

            df = pd.DataFrame(tracks_for_playlist,columns=['Name', 'ID', 'Duration(sec)', 'Tempo(bpm)'])
            tracks_ids_list = df['ID'].tolist()
            create_new_playlist(sp, USER_NAME, list_of_paces[i], DISTANCE_TIME[i][0], tracks_ids_list)




        return ("Completed Successfully")

    def get_token():
        token_info = session.get(TOKEN_INFO, None)
        if not token_info:
            redirect(url_for('login',_external=False))

        now = int(time.time())
        is_expired = token_info['expires_at'] - now < 60
        if(is_expired):
            spotify_oauth = create_spotify_oauth()
            token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

        return token_info

    def create_spotify_oauth():
        return SpotifyOAuth(client_id=client_id,
                            client_secret=client_secret,
                            redirect_uri=url_for('redirect_page',_external=True),
                            scope='user-library-read playlist-modify-public playlist-modify-private user-read-private'
                            )

    return app



app = create_app()
app.run(debug=True)