import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, process_data, sidebar_filters

st.set_page_config(
    page_title="Paris 2024 Olympics Dashboard",
    page_icon="🏅",
    layout="wide"
)

# Load and Process Data
data = load_data()
data = process_data(data)

# Sidebar Filters
selected_continent, selected_countries, selected_sports, selected_medal_types = sidebar_filters(data)

# Helper function to get countries from continent selection
def get_filtered_countries(data, selected_continent, selected_countries):
    if selected_countries:
        return selected_countries
    if selected_continent and 'nocs' in data:
        return data['nocs'][data['nocs']['Continent'].isin(selected_continent)]['country'].unique().tolist()
    return []

effective_countries = get_filtered_countries(data, selected_continent, selected_countries)

# Main Page Content
st.title("🏅 Paris 2024 Olympic Games Dashboard")
st.markdown("""
This dashboard provides a comprehensive overview of the Paris 2024 Olympic Games. 
Explore the data to uncover insights about athletes, countries, sports, and medal standings.
""")


st.header("Key Performance Indicators")

athletes_df = data.get('athletes', pd.DataFrame())
if not athletes_df.empty:
    if effective_countries:

        col = 'country' if 'country' in athletes_df.columns else 'noc'
        if col in athletes_df.columns:
            athletes_df = athletes_df[athletes_df[col].isin(effective_countries)]
    if selected_sports:

        col = 'sport' if 'sport' in athletes_df.columns else 'discipline'
        if col in athletes_df.columns:
            athletes_df = athletes_df[athletes_df[col].isin(selected_sports)]

total_athletes = len(athletes_df)


nocs_df = data.get('nocs', pd.DataFrame())
if not nocs_df.empty:
    if effective_countries:
        col = 'country' if 'country' in nocs_df.columns else 'noc'
        if col in nocs_df.columns:
            nocs_df = nocs_df[nocs_df[col].isin(effective_countries)]
total_countries = len(nocs_df)


events_df = data.get('events', pd.DataFrame())
if not events_df.empty:
    if selected_sports:
        events_df = events_df[events_df['sport'].isin(selected_sports)]
    total_sports = events_df['sport'].nunique() if 'sport' in events_df.columns else 0
    total_events = len(events_df)
else:
    total_sports = 0
    total_events = 0


medals_total_df = data.get('medals_total', pd.DataFrame())
total_medals_awarded = 0
if not medals_total_df.empty:

    if effective_countries:
        col = 'country' if 'country' in medals_total_df.columns else 'noc' # Check column name
        if col in medals_total_df.columns:
            medals_total_df = medals_total_df[medals_total_df[col].isin(effective_countries)]
    

    medal_mapping = {'Gold': 'Gold Medal', 'Silver': 'Silver Medal', 'Bronze': 'Bronze Medal'}
    medal_cols = [medal_mapping[m] for m in ['Gold', 'Silver', 'Bronze'] if m in selected_medal_types and medal_mapping[m] in medals_total_df.columns]
    
    if medal_cols:
        total_medals_awarded = medals_total_df[medal_cols].sum().sum()
    else:
        total_medals_awarded = 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Athletes", total_athletes)
col2.metric("Total Countries", total_countries)
col3.metric("Total Sports", total_sports)
col4.metric("Total Medals", int(total_medals_awarded))
col5.metric("Total Events", total_events)

col_viz1, col_viz2 = st.columns(2)

with col_viz1:
    st.subheader("Global Medal Distribution")
    medals_agg = data.get('medals_total', pd.DataFrame())

    if not medals_agg.empty:

        if effective_countries:
             col = 'country' if 'country' in medals_agg.columns else 'noc'
             if col in medals_agg.columns:
                medals_agg = medals_agg[medals_agg[col].isin(effective_countries)]
        

        medal_counts = {
            'Medal Type': [],
            'Count': []
        }
        medal_mapping = {'Gold': 'Gold Medal', 'Silver': 'Silver Medal', 'Bronze': 'Bronze Medal'}
        for m_type in ['Gold', 'Silver', 'Bronze']:
            col_name = medal_mapping.get(m_type)
            if col_name and col_name in medals_agg.columns:
                medal_counts['Medal Type'].append(m_type)
                medal_counts['Count'].append(medals_agg[col_name].sum())
        
        medal_dist_df = pd.DataFrame(medal_counts)
        

        medal_dist_df = medal_dist_df[medal_dist_df['Medal Type'].isin(selected_medal_types)]

        if not medal_dist_df.empty and medal_dist_df['Count'].sum() > 0:
            fig_pie = px.pie(medal_dist_df, values='Count', names='Medal Type', 
                             color='Medal Type',
                             color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'},
                             hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No medal data available for the current selection.")
    else:
        st.warning("Medals data not loaded.")


with col_viz2:
    st.subheader("Top 10 Countries by Medal Count")
    medals_standings = data.get('medals_total', pd.DataFrame())
    if not medals_standings.empty:
        
        if effective_countries:
             col = 'country' if 'country' in medals_standings.columns else 'noc'
             if col in medals_standings.columns:
                medals_standings = medals_standings[medals_standings[col].isin(effective_countries)]
        
        medal_mapping = {'Gold': 'Gold Medal', 'Silver': 'Silver Medal', 'Bronze': 'Bronze Medal'}
        medal_cols = [medal_mapping[m] for m in ['Gold', 'Silver', 'Bronze'] if m in selected_medal_types and medal_mapping[m] in medals_standings.columns]
        
        if medal_cols:
            medals_standings['Selected Total'] = medals_standings[medal_cols].sum(axis=1)
        if medal_cols:
            medals_standings['Selected Total'] = medals_standings[medal_cols].sum(axis=1)
            
            top_10 = medals_standings.sort_values(by='Selected Total', ascending=False).head(10)
            
            if not top_10.empty:
                fig_bar = px.bar(top_10, x='Selected Total', y='country', orientation='h',
                                 text='Selected Total',
                                 labels={'Selected Total': 'Total Medals', 'country': 'Country'},
                                 color='Selected Total',
                                 color_continuous_scale='Viridis')
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No data for top 10.")
        else:
            st.info("Select at least one medal type.")
    else:
        st.warning("Medals data not loaded.")
