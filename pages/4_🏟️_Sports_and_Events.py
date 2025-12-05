import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import load_data, process_data, sidebar_filters

st.set_page_config(page_title="Sports and Events", page_icon="🏟️", layout="wide")

# Load Data
data = load_data()
data = process_data(data)

# Sidebar Filters
selected_continent, selected_countries, selected_sports, selected_medal_types = sidebar_filters(data)

def get_filtered_countries(data, selected_continent, selected_countries):
    if selected_countries:
        return selected_countries
    if selected_continent and 'nocs' in data:
        return data['nocs'][data['nocs']['Continent'].isin(selected_continent)]['country'].unique().tolist()
    return []

effective_countries = get_filtered_countries(data, selected_continent, selected_countries)

st.title("🏟️ Sports and Events")

schedule_df = data.get('schedules', pd.DataFrame())
events_df = data.get('events', pd.DataFrame())
venues_df = data.get('venues', pd.DataFrame())
medals_df = data.get('medals', pd.DataFrame())

# 1. Event Schedule (Gantt Chart)
st.subheader("Event Schedule")
if not schedule_df.empty:
    # Filter by sport
    sched_viz = schedule_df.copy()
    if selected_sports:
        if 'discipline' in sched_viz.columns:
            sched_viz = sched_viz[sched_viz['discipline'].isin(selected_sports)]
    
    date_col = 'start_date'
        
    if date_col:
        sched_viz[date_col] = pd.to_datetime(sched_viz[date_col])
        # Create a dummy end date if not present (e.g. + 2 hours)
        if 'end_date' not in sched_viz.columns:
            sched_viz['end_date'] = sched_viz[date_col] + pd.Timedelta(hours=2)
        else:
            sched_viz['end_date'] = pd.to_datetime(sched_viz['end_date'])
            
        # Use 'discipline' for y-axis and color
        y_col = 'discipline'
        
        fig_gantt = px.timeline(sched_viz, x_start=date_col, x_end='end_date', y=y_col, color=y_col,
                                title="Event Schedule")
        st.plotly_chart(fig_gantt, use_container_width=True)
    else:
        st.warning("Date columns not found in schedule data.")
else:
    st.info("Schedule data not available.")

st.subheader("Medal Count by Sport")
if not medals_df.empty:
    # Group by Sport (discipline)
    medals_viz = medals_df.copy()
    if effective_countries:
        medals_viz = medals_viz[medals_viz['country'].isin(effective_countries)]
            
    sport_medals = medals_viz['discipline'].value_counts().reset_index()
    sport_medals.columns = ['Sport', 'Count']
    
    if not sport_medals.empty:
        fig_tree = px.treemap(sport_medals, path=['Sport'], values='Count', title="Medals by Sport")
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.info("No medals data available for the current selection.")
else:
    st.info("Medals data not available.")

# 3. Venue Map
st.subheader("Olympic Venues")

# Hardcoded coordinates for venues since they are missing in the dataset
venue_coordinates = {
    "Aquatics Centre": [48.9244, 2.3600],
    "Bercy Arena": [48.8387, 2.3785],
    "Bordeaux Stadium": [44.8969, -0.5633],
    "Champ de Mars Arena": [48.8546, 2.3015],
    "Château de Versailles": [48.8049, 2.1204],
    "Chateauroux Shooting Centre": [46.8115, 1.7211],
    "Eiffel Tower Stadium": [48.8584, 2.2945],
    "Elancourt Hill": [48.7708, 1.9683],
    "Geoffroy-Guichard Stadium": [45.4608, 4.3903],
    "Grand Palais": [48.8661, 2.3125],
    "Hôtel de Ville": [48.8566, 2.3522],
    "Invalides": [48.8622, 2.3125],
    "La Beaujoire Stadium": [47.2556, -1.5253],
    "La Concorde": [48.8655, 2.3212],
    "Le Bourget Sport Climbing Venue": [48.9394, 2.4250],
    "Golf National": [48.7544, 2.0758],
    "Lyon Stadium": [45.7653, 4.9820],
    "Marseille Marina": [43.2694, 5.3714],
    "Marseille Stadium": [43.2699, 5.3959],
    "Nice Stadium": [43.7053, 7.1925],
    "North Paris Arena": [48.9717, 2.5161],
    "Parc des Princes": [48.8414, 2.2530],
    "Paris La Defense Arena": [48.8958, 2.2297],
    "Pierre Mauroy Stadium": [50.6119, 3.1305],
    "Pont Alexandre III": [48.8639, 2.3136],
    "Porte de La Chapelle Arena": [48.8994, 2.3603],
    "Stade Roland-Garros": [48.8472, 2.2492],
    "Saint-Quentin-en-Yvelines BMX Stadium": [48.7880, 2.0367],
    "Saint-Quentin-en-Yvelines Velodrome": [48.7880, 2.0367],
    "South Paris Arena": [48.8325, 2.2861],
    "Stade de France": [48.9246, 2.3602],
    "Teahupo'o, Tahiti": [-17.8472, -149.2667],
    "Trocadéro": [48.8629, 2.2872],
    "Vaires-sur-Marne Nautical Stadium": [48.8617, 2.6378],
    "Yves-du-Manoir Stadium": [48.9294, 2.2483]
}

if not venues_df.empty:

    lat_col = 'latitude' if 'latitude' in venues_df.columns else 'lat'
    lon_col = 'longitude' if 'longitude' in venues_df.columns else 'lon'
    
    if lat_col not in venues_df.columns or lon_col not in venues_df.columns:
        venues_df['lat'] = venues_df['venue'].map(lambda x: venue_coordinates.get(x, [None, None])[0])
        venues_df['lon'] = venues_df['venue'].map(lambda x: venue_coordinates.get(x, [None, None])[1])
        lat_col = 'lat'
        lon_col = 'lon'

    if lat_col in venues_df.columns and lon_col in venues_df.columns:
        # Filter out venues with no coordinates
        venues_map = venues_df.dropna(subset=[lat_col, lon_col])
        
        if not venues_map.empty:
            fig_map = px.scatter_mapbox(venues_map, lat=lat_col, lon=lon_col, hover_name='venue',
                                        zoom=4, height=500) # Zoom out to see Tahiti
            fig_map.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig_map, use_container_width=True)
        else:
             st.warning("Could not map venues to coordinates.")
             st.dataframe(venues_df[['venue', 'sports', 'date_start', 'date_end', 'url']], use_container_width=True)
    else:
        st.warning("Latitude/Longitude columns not found in venues data. Displaying venue list instead.")
        st.dataframe(venues_df[['venue', 'sports', 'date_start', 'date_end', 'url']], use_container_width=True)
else:
    st.info("Venues data not available.")
