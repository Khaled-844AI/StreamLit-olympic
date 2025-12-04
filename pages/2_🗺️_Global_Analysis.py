import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import load_data, process_data, sidebar_filters

st.set_page_config(page_title="Global Analysis", page_icon="🗺️", layout="wide")

data = load_data()
data = process_data(data)

selected_continent, selected_countries, selected_sports, selected_medal_types = sidebar_filters(data)

def get_filtered_countries(data, selected_continent, selected_countries):
    if selected_countries:
        return selected_countries
    if selected_continent and 'nocs' in data:
        return data['nocs'][data['nocs']['Continent'].isin(selected_continent)]['country'].unique().tolist()
    return []

effective_countries = get_filtered_countries(data, selected_continent, selected_countries)

st.title("🗺️ Global Analysis")


medals_total = data.get('medals_total', pd.DataFrame())
nocs = data.get('nocs', pd.DataFrame())

if not medals_total.empty and not nocs.empty:

    if 'country' in medals_total.columns and 'country' in nocs.columns:
        merged_df = pd.merge(medals_total, nocs, on='country', how='left')
    elif 'country_code' in medals_total.columns and 'code' in nocs.columns:
        merged_df = pd.merge(medals_total, nocs, left_on='country_code', right_on='code', how='left')
    else:
        merged_df = medals_total.copy()
        st.error("Could not merge medals and NOCs data. Check column names.")


    if effective_countries:
        merged_df = merged_df[merged_df['country'].isin(effective_countries)]
    
    # Calculate Total Medals based on selection
    medal_mapping = {'Gold': 'Gold Medal', 'Silver': 'Silver Medal', 'Bronze': 'Bronze Medal'}
    medal_cols = [medal_mapping[m] for m in ['Gold', 'Silver', 'Bronze'] if m in selected_medal_types and medal_mapping[m] in merged_df.columns]

    if medal_cols:
        merged_df['Filtered_Total'] = merged_df[medal_cols].sum(axis=1)
    else:
        merged_df['Filtered_Total'] = 0

    st.subheader("World Medal Map")
    if not merged_df.empty:
        fig_map = px.choropleth(merged_df, 
                                locations="country", 
                                locationmode='country names',
                                color="Filtered_Total",
                                hover_name="country",
                                color_continuous_scale=px.colors.sequential.Plasma,
                                title="Total Medals by Country")
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No data available for map.")

    st.subheader("Medal Hierarchy by Continent")

    medals_individual = data.get('medals', pd.DataFrame())
    
    if not medals_individual.empty and not nocs.empty:

        if 'country_code' in medals_individual.columns and 'code' in nocs.columns:
             medals_ind_merged = pd.merge(medals_individual, nocs, left_on='country_code', right_on='code', how='left')
        elif 'country' in medals_individual.columns and 'country' in nocs.columns:
             medals_ind_merged = pd.merge(medals_individual, nocs, on='country', how='left')
        else:
             medals_ind_merged = pd.DataFrame()

        if not medals_ind_merged.empty:

            if 'country' not in medals_ind_merged.columns and 'country_x' in medals_ind_merged.columns:
                medals_ind_merged = medals_ind_merged.rename(columns={'country_x': 'country'})
            
            # Filter
            if effective_countries:
                if 'country' in medals_ind_merged.columns:
                    medals_ind_merged = medals_ind_merged[medals_ind_merged['country'].isin(effective_countries)]
            if selected_sports:
                if 'discipline' in medals_ind_merged.columns:
                    medals_ind_merged = medals_ind_merged[medals_ind_merged['discipline'].isin(selected_sports)] # Assuming 'discipline' or 'sport'
            
            # Filter by medal type
            if 'medal_type' in medals_ind_merged.columns:
                 medal_mapping = {'Gold': 'Gold Medal', 'Silver': 'Silver Medal', 'Bronze': 'Bronze Medal'}
                 selected_medal_values = [medal_mapping[m] for m in selected_medal_types if m in medal_mapping]
                 medals_ind_merged = medals_ind_merged[medals_ind_merged['medal_type'].isin(selected_medal_values)]
            
            # Group for Hierarchy

            if 'Continent' in medals_ind_merged.columns and 'country' in medals_ind_merged.columns and 'discipline' in medals_ind_merged.columns:
                hierarchy_df = medals_ind_merged.groupby(['Continent', 'country', 'discipline']).size().reset_index(name='Medal Count')
                
                if not hierarchy_df.empty:
                    chart_type = st.radio("Select Chart Type", ["Sunburst", "Treemap"], horizontal=True)
                    
                    if chart_type == "Sunburst":
                        fig_hier = px.sunburst(hierarchy_df, path=['Continent', 'country', 'discipline'], values='Medal Count',
                                              title="Medal Distribution Hierarchy (Sunburst)")
                    else:
                        fig_hier = px.treemap(hierarchy_df, path=['Continent', 'country', 'discipline'], values='Medal Count',
                                              title="Medal Distribution Hierarchy (Treemap)")
                        
                    st.plotly_chart(fig_hier, use_container_width=True)
                else:
                    st.info("No data for Hierarchy chart.")
            else:
                st.warning("Missing columns for Hierarchy (Continent, country, discipline).")
    else:
        st.info("Detailed medal data not available for hierarchy.")

    # 3. Continent vs. Medals Bar Chart
    st.subheader("Medals by Continent")
    if 'Continent' in merged_df.columns:
        # Map selected medal types to actual columns
        medal_mapping = {'Gold': 'Gold Medal', 'Silver': 'Silver Medal', 'Bronze': 'Bronze Medal'}
        
        # Columns to group by
        agg_cols = {medal_mapping[m]: 'sum' for m in ['Gold', 'Silver', 'Bronze'] if medal_mapping[m] in merged_df.columns}
        
        if agg_cols:
            continent_medals = merged_df.groupby('Continent').agg(agg_cols).reset_index()
            
 
            reverse_mapping = {v: k for k, v in medal_mapping.items()}
            continent_medals = continent_medals.rename(columns=reverse_mapping)
            
            # Melt for grouped bar chart
            available_medals = [m for m in ['Gold', 'Silver', 'Bronze'] if m in continent_medals.columns]
            continent_melted = continent_medals.melt(id_vars='Continent', value_vars=available_medals, 
                                                     var_name='Medal Type', value_name='Count')
            # Filter by selected medal types
            continent_melted = continent_melted[continent_melted['Medal Type'].isin(selected_medal_types)]
            
            if not continent_melted.empty:
                fig_cont = px.bar(continent_melted, x='Continent', y='Count', color='Medal Type', barmode='group',
                                  color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'})
                st.plotly_chart(fig_cont, use_container_width=True)
            else:
                st.info("No data for Continent chart.")
        else:
             st.info("No medal columns found for aggregation.")
    else:
        st.warning("Continent data not available.")

    st.subheader("Top 20 Countries Medal Breakdown")
    if not merged_df.empty:
        top_20 = merged_df.sort_values(by='Filtered_Total', ascending=False).head(20)
        
        # Map selected medal types to actual columns
        medal_mapping = {'Gold': 'Gold Medal', 'Silver': 'Silver Medal', 'Bronze': 'Bronze Medal'}
        
        # Rename columns for melting
        reverse_mapping = {v: k for k, v in medal_mapping.items() if v in top_20.columns}
        top_20 = top_20.rename(columns=reverse_mapping)
        
        # Melt
        available_medals = [m for m in ['Gold', 'Silver', 'Bronze'] if m in top_20.columns]
        
        if available_medals:
            top_20_melted = top_20.melt(id_vars='country', value_vars=available_medals, 
                                        var_name='Medal Type', value_name='Count')
            top_20_melted = top_20_melted[top_20_melted['Medal Type'].isin(selected_medal_types)]
            
            if not top_20_melted.empty:
                fig_top20 = px.bar(top_20_melted, x='country', y='Count', color='Medal Type', 
                                   title="Top 20 Countries by Medal Count",
                                   color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'})
                st.plotly_chart(fig_top20, use_container_width=True)
            else:
                st.info("No data for Top 20 chart.")
        else:
             st.info("No medal data available for Top 20.")

else:
    st.error("Required datasets (medals_total, nocs) not found.")
