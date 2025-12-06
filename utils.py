import streamlit as st
import pandas as pd
import os
import pycountry_convert as pc
import ast

DATA_FOLDER = 'data'

@st.cache_data
def load_data():
    """Loads all necessary datasets from the data folder."""
    data = {}
    files = [
        'athletes.csv', 'coaches.csv', 'events.csv', 'medals.csv', 
        'medals_total.csv', 'medallists.csv', 'nocs.csv', 'schedules.csv', 
        'schedules_preliminary.csv', 'teams.csv', 'technical_officials.csv', 
        'torch_route.csv', 'venues.csv'
    ]
    
    for file in files:
        path = os.path.join(DATA_FOLDER, file)
        if os.path.exists(path):
            try:
                data[file.split('.')[0]] = pd.read_csv(path)
            except Exception as e:
                st.error(f"Error loading {file}: {e}")
        else:
            st.warning(f"File {file} not found in {DATA_FOLDER}")
            #empty dataframe with expected columns to prevent crashes if file missing
            data[file.split('.')[0]] = pd.DataFrame()

    return data

def get_continent(country_name):
    try:
        country_code = pc.country_name_to_country_alpha2(country_name, cn_name_format="default")
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name
    except:
        return "Unknown"

@st.cache_data
def process_data(data):
    """Pre-process data, e.g., adding continent information."""

    if 'nocs' in data and not data['nocs'].empty:
        data['nocs']['Continent'] = data['nocs']['country'].apply(get_continent)

    return data

def sidebar_filters(data):
    """Creates global sidebar filters and returns selected values."""
    st.sidebar.header("Global Filters")
    
    selected_continent = []
    selected_country = []
    selected_sport = []
    selected_medal_type = []

    # Continent Filter
    if 'nocs' in data and not data['nocs'].empty and 'Continent' in data['nocs'].columns:
        continents = sorted(data['nocs']['Continent'].dropna().unique())
        selected_continent = st.sidebar.multiselect("Select Continent", continents)

    # Country Filter
    if 'nocs' in data and not data['nocs'].empty:
        df_countries = data['nocs']
        if selected_continent:
            df_countries = df_countries[df_countries['Continent'].isin(selected_continent)]
            
        countries = sorted(df_countries['country'].unique()) if 'country' in df_countries.columns else []
        selected_country = st.sidebar.multiselect("Select Country (NOC)", countries)
    
    # Sport Filter
    if 'events' in data and not data['events'].empty:
        sports = sorted(data['events']['sport'].unique()) if 'sport' in data['events'].columns else []
        selected_sport = st.sidebar.multiselect("Select Sport", sports)

    # Medal Type Filter
    medal_types = ['Gold', 'Silver', 'Bronze']
    selected_medal_type = []
    st.sidebar.write("Select Medal Type")
    for medal in medal_types:
        if st.sidebar.checkbox(medal, value=True):
            selected_medal_type.append(medal)
            
    return selected_continent, selected_country, selected_sport, selected_medal_type




def safe_parse(val):

    if isinstance(val, list):
        return val
    
    val = str(val)
    
    try:
        parsed = ast.literal_eval(val)
        return parsed if isinstance(parsed, list) else [parsed]
    except:
        return []
