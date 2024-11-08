'''Copyright 2024 Ashok Kumar

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.'''


import requests
import json
import pandas as pd
import geopandas as gpd
import contextily as ctx
import tzlocal
import pytz
from PIL import Image
from datetime import datetime
import matplotlib.pyplot as plt
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
import warnings
warnings.filterwarnings('ignore')
from plotly.graph_objs import Marker
import plotly.express as px

def flight_data(flight_view_level, country, local_time_zone, flight_info, airport):
    geolocator = Nominatim(user_agent="flight_tracker")
    loc = geolocator.geocode(country)
    loc_box = loc[1]
    extend_left =+12*flight_view_level
    extend_right =+10*flight_view_level
    extend_top =+10*flight_view_level
    extend_bottom =+ 18*flight_view_level
    lat_min, lat_max = (loc_box[0] - extend_left), loc_box[0]+extend_right
    lon_min, lon_max = (loc_box[1] - extend_bottom), loc_box[1]+extend_top

    tile_zoom = 8 # zoom of the map loaded by contextily
    figsize = (15, 15)
    columns = ["icao24","callsign","origin_country","time_position","last_contact","longitude","latitude",
            "baro_altitude","on_ground","velocity","true_track","vertical_rate","sensors","geo_altitude",
            "squawk","spi","position_source",]
    data_url = "https://raw.githubusercontent.com/ashok2216-A/ashok_airport-data/main/data/airports.dat"
    column_names = ["Airport ID", "Name", "City", "Country", "IATA/FAA", "ICAO", "Latitude", "Longitude",
                    "Altitude", "Timezone", "DST", "Tz database time zone", "Type", "Source"]
    airport_df = pd.read_csv(data_url, header=None, names=column_names)
    airport_locations = airport_df[["Name", "City", "Country", "IATA/FAA", "Latitude", "Longitude"]]
    airport_country_loc = airport_locations[airport_locations['Country'] == str(loc)]
    airport_country_loc = airport_country_loc[(airport_country_loc['Country'] == str(loc)) & (airport_country_loc['Latitude'] >= lat_min) &
                            (airport_country_loc['Latitude'] <= lat_max) & (airport_country_loc['Longitude'] >= lon_min) &
                            (airport_country_loc['Longitude'] <= lon_max)]

    url_data = (
            f"https://@opensky-network.org/api/states/all?"
            f"lamin={str(lat_min)}"
            f"&lomin={str(lon_min)}"
            f"&lamax={str(lat_max)}"
            f"&lomax={str(lon_max)}")
    json_dict = requests.get(url_data).json()

    unix_timestamp = int(json_dict["time"])
    local_timezone = pytz.timezone(local_time_zone) # get pytz timezone
    local_time = datetime.fromtimestamp(unix_timestamp, local_timezone).strftime('%Y-%m-%d %H:%M:%S')
    time = []
    for i in range(len(json_dict['states'])):
        time.append(local_time)
    df_time = pd.DataFrame(time,columns=['time'])
    state_df = pd.DataFrame(json_dict["states"],columns=columns)
    state_df['time'] = df_time
    gdf = gpd.GeoDataFrame(
            state_df,
            geometry=gpd.points_from_xy(state_df.longitude, state_df.latitude),
            crs={"init": "epsg:4326"},  # WGS84
        )
    return gdf
# geo_df = flight_tracking(flight_view_level = 6, country= 'India', local_time_zone='Asia/Kolkata', flight_info='baro_altitude', airport=1)
