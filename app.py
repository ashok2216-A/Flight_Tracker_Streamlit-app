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
import streamlit as st


def flight_tracking(flight_view_level, country, local_time_zone, flight_info, airport, color):
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
    def get_traffic_gdf():
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
        # banner_image = Image.open('banner.png')
        # st.image(banner_image, width=300)
        st.title("Live Flight Tracker")
        st.subheader('Flight Details', divider='rainbow')
        st.write('Location: {0}'.format(loc))
        st.write('Current Local Time: {0}-{1}:'.format(local_time, local_time_zone))
        st.write("Minimum_latitude is {0} and Maximum_latitude is {1}".format(lat_min, lat_max))
        st.write("Minimum_longitude is {0} and Maximum_longitude is {1}".format(lon_min, lon_max))
        st.write('Number of Visible Flights: {}'.format(len(json_dict['states'])))
        st.write('Plotting the flight: {}'.format(flight_info))
        st.subheader('Map Visualization', divider='rainbow')
        st.write('****Click ":orange[Update Map]" Button to Refresh the Map****')
        return gdf

    geo_df = get_traffic_gdf()
    if airport == 0:
        fig = px.scatter_mapbox(geo_df, lat="latitude", lon="longitude",color=flight_info,
                            color_continuous_scale=color, zoom=4,width=1200, height=600,opacity=1,
                            hover_name ='origin_country',hover_data=['callsign', 'baro_altitude',
        'on_ground', 'velocity', 'true_track', 'vertical_rate', 'geo_altitude'], template='plotly_dark')
    elif airport == 1:
        fig = px.scatter_mapbox(geo_df, lat="latitude", lon="longitude",color=flight_info,
                            color_continuous_scale=color, zoom=4,width=1200, height=600,opacity=1,
                            hover_name ='origin_country',hover_data=['callsign', 'baro_altitude',
        'on_ground', 'velocity', 'true_track', 'vertical_rate', 'geo_altitude'], template='plotly_dark')
        fig.add_trace(px.scatter_mapbox(airport_country_loc, lat="Latitude", lon="Longitude",
                                        hover_name ='Name', hover_data=["City", "Country", "IATA/FAA"]).data[0])
    else: None
    fig.update_layout(mapbox_style="carto-darkmatter")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    # out = fig.show())
    out = st.plotly_chart(fig, theme=None)
    return out
st.set_page_config(
    layout="wide"
)
image = Image.open('logo.png')
add_selectbox = st.sidebar.image(
    image, width=150
)
add_selectbox = st.sidebar.subheader(
    "Configure Map",divider='rainbow'
)
with st.sidebar:
    Refresh = st.button('Update Map', key=1)
    on = st.toggle('View Airports')
    if on:
        air_port = 1
        st.write(':rainbow[Nice Work Buddy!]')
        st.write('Now Airports are Visible')
    else:
        air_port=0
    view = st.slider('Increase Flight Visibility',1,6,2)
    st.write("You Selected:", view)
    cou = st.text_input('Type Country Name', 'india')
    st.write('The current Country name is', cou)
    time = st.text_input('Type Time Zone Name (Ex: America/Toronto, Europe/Berlin)', 'Asia/Kolkata')
    st.write('The current Time Zone is', time)
    info = st.selectbox(
    'Select Flight Information',
    ('baro_altitude',
        'on_ground', 'velocity',
        'geo_altitude'))
    st.write('Plotting the data of Flight:', info)
    clr = st.radio('Pick A Color for Scatter Plot',["rainbow","ice","hot"])
    if clr == "rainbow":
        st.write('The current color is', "****:rainbow[Rainbow]****")
    elif clr == 'ice':
        st.write('The current color is', "****:blue[Ice]****")
    elif clr == 'hot':
        st.write('The current color is', "****:red[Hot]****")
    else: None

try:
    flight_tracking(flight_view_level=view, country=cou,flight_info=info,
                local_time_zone=time, airport=air_port, color=clr)
except TypeError:
    st.error(':red[Error: ] Please Re-run this page.', icon="🚨")
