import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import load_data, process_data, sidebar_filters

st.set_page_config(page_title="Athlete Performance", page_icon="👤", layout="wide")

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

st.title("👤 Athlete Performance")

athletes_df = data.get('athletes', pd.DataFrame())
coaches_df = data.get('coaches', pd.DataFrame())
medals_df = data.get('medals', pd.DataFrame()) 
nocs_df = data.get('nocs', pd.DataFrame())

if not athletes_df.empty:

    filtered_athletes = athletes_df.copy()
    
    filtered_athletes['sport'] = filtered_athletes['disciplines'].astype(str).str.replace(r"[\[\]']", "", regex=True)

    if effective_countries:
        filtered_athletes = filtered_athletes[filtered_athletes['country'].isin(effective_countries)]
    if selected_sports:
        filtered_athletes = filtered_athletes[filtered_athletes['sport'].isin(selected_sports)]

    # 1. Athlete Detailed Profile Card
    st.subheader("Athlete Profile")
    
    # Search box
    athlete_names = sorted(filtered_athletes['name'].unique()) if 'name' in filtered_athletes.columns else []
    selected_athlete_name = st.selectbox("Search and Select an Athlete", ["Select an Athlete"] + athlete_names)

    if selected_athlete_name != "Select an Athlete":
        athlete_info = filtered_athletes[filtered_athletes['name'] == selected_athlete_name].iloc[0]
        
        col1, col2 = st.columns([1, 3])
        
        with col1:

            st.image("https://via.placeholder.com/150", caption=selected_athlete_name, width=150)
        
        with col2:
            st.markdown(f"### {athlete_info['name']}")
            st.write(f"**Country:** {athlete_info.get('country', 'N/A')}")
            st.write(f"**Sport:** {athlete_info.get('sport', 'N/A')}")
            st.write(f"**Discipline:** {athlete_info.get('disciplines', 'N/A')}")
            
            height = athlete_info.get('height', 0)
            weight = athlete_info.get('weight', 0)
            st.write(f"**Height:** {height if height > 0 else 'N/A'}")
            st.write(f"**Weight:** {weight if weight > 0 else 'N/A'}")
            
            coach = athlete_info.get('coach', 'N/A')
            if pd.isna(coach) or coach == '':
                coach = 'N/A'
            st.write(f"**Coach:** {coach}")

    st.divider()

    # 2. Athlete Age Distribution
    st.subheader("Athlete Age Distribution")
    if 'age' in filtered_athletes.columns or 'birth_date' in filtered_athletes.columns:
        # Calculate age if needed
        if 'age' not in filtered_athletes.columns and 'birth_date' in filtered_athletes.columns:
            filtered_athletes['birth_date'] = pd.to_datetime(filtered_athletes['birth_date'], errors='coerce')
            filtered_athletes['age'] = 2024 - filtered_athletes['birth_date'].dt.year
        
        if 'age' in filtered_athletes.columns:
            fig_age = px.box(filtered_athletes, x='sport', y='age', color='gender', 
                             title="Age Distribution by Sport and Gender")
            st.plotly_chart(fig_age, use_container_width=True)
        else:
            st.info("Age data not available.")
    else:
        st.info("Age data not available.")

    # 3. Gender Distribution
    st.subheader("Gender Distribution")
    view_mode = st.radio("View Gender Distribution By:", ["World", "Continent", "Country"])
    
    gender_df = filtered_athletes.copy()
    
    if view_mode == "Continent":
        if not nocs_df.empty:
             if 'country' in gender_df.columns and 'country' in nocs_df.columns:
                gender_df = pd.merge(gender_df, nocs_df[['country', 'Continent']], on='country', how='left')
             
             selected_cont = st.selectbox("Select Continent", gender_df['Continent'].dropna().unique())
             gender_df = gender_df[gender_df['Continent'] == selected_cont]
        else:
            st.warning("Continent data not available.")

    elif view_mode == "Country":
        selected_ctry = st.selectbox("Select Country", gender_df['country'].unique())
        gender_df = gender_df[gender_df['country'] == selected_ctry]

    if not gender_df.empty and 'gender' in gender_df.columns:
        gender_counts = gender_df['gender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']
        fig_gender = px.pie(gender_counts, values='Count', names='Gender', title=f"Gender Distribution ({view_mode})")
        st.plotly_chart(fig_gender, use_container_width=True)
    else:
        st.info("No gender data available for selection.")

    # 4. Top Athletes by Medals
    st.subheader("Top 10 Athletes by Medal Count")
    if not medals_df.empty:
        filtered_medals = medals_df.copy()
        
        if effective_countries:
            if 'country' in filtered_medals.columns:
                filtered_medals = filtered_medals[filtered_medals['country'].isin(effective_countries)]
        
        if selected_sports:
            if 'discipline' in filtered_medals.columns:
                filtered_medals = filtered_medals[filtered_medals['discipline'].isin(selected_sports)]
        
        if not filtered_medals.empty:
            # Count medals per athlete
            athlete_medals = filtered_medals['name'].value_counts().reset_index()
            athlete_medals.columns = ['name', 'Medal Count']
            
            top_athletes = athlete_medals.head(10)
            
            fig_top_ath = px.bar(top_athletes, x='Medal Count', y='name', orientation='h',
                                 title="Top 10 Athletes by Total Medals")
            fig_top_ath.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top_ath, use_container_width=True)
        else:
            st.info("No medals found for the current selection.")
    else:
        st.info("Medal data not available.")

else:
    st.error("Athletes data not found.")
