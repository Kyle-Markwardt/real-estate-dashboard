import streamlit as st
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.preprocessing import LabelEncoder


# Load Data
def load_data():
    data = pd.read_csv('Data/sfo_neighborhoods_census_data.csv')
    locations = pd.read_csv('Data/neighborhoods_coordinates.csv')
    return data, locations

sfo_data, locations = load_data()

# Get unique neighborhoods for the dropdown
neighborhoods = sfo_data['neighborhood'].unique()

locations.rename(columns={'Neighborhood': 'neighborhood'}, inplace=True)

# Visualization Functions
def housing_units_per_year():
    units_per_year = sfo_data.groupby('year').mean('housing_units')[['housing_units']]
    fig = px.bar(units_per_year, y='housing_units', title='Average Housing Units Per Year')
    std_dev = units_per_year['housing_units'].std()
    min_units = units_per_year['housing_units'].min() - std_dev
    max_units = units_per_year['housing_units'].max() + std_dev
    fig.update_layout(
    yaxis=dict(range=[min_units, max_units])
)
    return fig

def average_gross_rent():
    costs = sfo_data.groupby('year').mean(['gross_rent'])
    fig = px.line(costs, y='gross_rent', title='Average Gross Rent by Year')
    return fig

def average_sales_price():
    costs = sfo_data.groupby('year').mean(['sale_price_sqr_foot'])
    fig = px.line(costs, y='sale_price_sqr_foot', title='Average Sale Price per Square Foot by Year')
    return fig

def average_price_by_neighborhood(neighborhood):
    df_prices = sfo_data[sfo_data['neighborhood'] == neighborhood]
    df_avg_price_per_year = df_prices.groupby('year')['sale_price_sqr_foot'].mean().reset_index()
    fig = px.line(df_avg_price_per_year, x='year', y='sale_price_sqr_foot',
                  title=f'Average Sale Price per Square Foot in {neighborhood}')
    return fig

def top_most_expensive_neighborhoods():
    df_mean_price = sfo_data.groupby(['year', 'neighborhood'])['sale_price_sqr_foot'].mean().reset_index()
    df_top_10 = df_mean_price.groupby('neighborhood')['sale_price_sqr_foot'].mean().nlargest(10).reset_index()
    fig = px.bar(df_top_10, x='neighborhood', y='sale_price_sqr_foot',
                 title='Top 10 Most Expensive Neighborhoods in San Francisco')
    return fig

def most_expensive_neighborhoods_rent_sales(neighborhood):
    df_costs = sfo_data[sfo_data['neighborhood'] == neighborhood]
    df_costs.reset_index(inplace=True)
    df_costs = df_costs[['year', 'sale_price_sqr_foot', 'gross_rent']].melt(id_vars='year', var_name='Cost Type', value_name='Value')
    fig = px.bar(df_costs, x='year', y='Value', color='Cost Type', barmode='group',
            title=f'Sale Price per Square Foot and Gross Rent in {neighborhood}')
    
    fig.update_layout(xaxis_title='Year', yaxis_title='Cost')
    return fig

# Helper Functions for Data Processing
def prepare_data():
    # Prepare the neighborhood average data
    df_neighborhood_mean = sfo_data.groupby('neighborhood').mean().reset_index()
    df_neighborhood_mean.dropna(inplace=True)

    df_neighborhood_mean['neighborhood'] = df_neighborhood_mean['neighborhood'].str.strip()
    locations['neighborhood'] = locations['neighborhood'].str.strip()

    # Join average values with neighborhood locations
    df_map_data = df_neighborhood_mean.join(locations.set_index('neighborhood'), on='neighborhood', how='outer')
    return df_map_data

def neighborhood_map():
    df_map_data = prepare_data()
    fig = px.scatter_mapbox(df_map_data, lat="Lat", lon="Lon", hover_name="neighborhood",
                            hover_data=["sale_price_sqr_foot"], color="sale_price_sqr_foot", size="sale_price_sqr_foot",
                            color_continuous_scale=px.colors.diverging.RdYlGn[::-1], size_max=25, zoom=11,
                            title="Average Sale Price per Square Foot by Neighborhood")
    fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
    return fig

def parallel_categories_plot():
    df_expensive_neighborhoods = sfo_data.groupby(by="neighborhood").mean().sort_values(
        by="sale_price_sqr_foot", ascending=False).head(10).reset_index()
    fig = px.parallel_categories(df_expensive_neighborhoods, 
                                 dimensions=['neighborhood', 'sale_price_sqr_foot', 'housing_units', 'gross_rent'],
                                 color='sale_price_sqr_foot', color_continuous_scale=px.colors.diverging.Tealrose)
    return fig

def parallel_coordinates_plot():
    all_data = sfo_data.join(locations.set_index('neighborhood'), on='neighborhood', how='outer').dropna()
    df_coor = all_data.groupby('neighborhood').mean()
    fig = px.parallel_coordinates(df_coor, color='sale_price_sqr_foot', 
                                  dimensions=['sale_price_sqr_foot', 'housing_units', 'gross_rent'],
                                  labels={
                                      'sale_price_sqr_foot': 'Sale Price per Square Foot',
                                      'housing_units': 'Housing Units',
                                      'gross_rent': 'Gross Rent'
                                  }, color_continuous_scale=px.colors.sequential.Viridis)
    return fig

def sunburst_plot():
    df_mean_price = sfo_data.groupby(['year', 'neighborhood'])['sale_price_sqr_foot'].mean().reset_index()
    df_top_7 = df_mean_price.groupby('year').apply(lambda x: x.nlargest(7, 'sale_price_sqr_foot')).reset_index(drop=True)
    fig = px.sunburst(df_top_7, path=['year', 'neighborhood'], values='sale_price_sqr_foot',
                      title='Costs Analysis of Most Expensive Neighborhoods in San Francisco Per Year',
                      color='year', color_continuous_scale=px.colors.sequential.Viridis[::-1])
    fig.update_layout(margin=dict(t=50, l=0, r=0, b=0))
    return fig

# Start Streamlit App
def main():
    st.title("San Francisco Housing Cost Analysis Dashboard")
    st.sidebar.title("Options")

    analysis_type = st.sidebar.radio(
        "Choose the Analysis Type:",
        ("Housing Units Per Year", "Average Gross Rent", "Average Sales Price", "Average Price by Neighborhood",
         "Top 10 Most Expensive Neighborhoods", "Most Expensive Neighborhoods Rent vs. Sales", "Neighborhood Map",
         "Parallel Categories Plot", "Parallel Coordinates Plot", "Sunburst Plot")
    )

    if analysis_type == "Housing Units Per Year":
        st.plotly_chart(housing_units_per_year())
    elif analysis_type == "Average Gross Rent":
        st.plotly_chart(average_gross_rent())
    elif analysis_type == "Average Sales Price":
        st.plotly_chart(average_sales_price())
    elif analysis_type == "Average Price by Neighborhood":
        neighborhood = st.sidebar.selectbox("Enter Neighborhood:", neighborhoods, index=neighborhoods.tolist().index("North Beach"))
        st.plotly_chart(average_price_by_neighborhood(neighborhood))
    elif analysis_type == "Top 10 Most Expensive Neighborhoods":
        st.plotly_chart(top_most_expensive_neighborhoods())
    elif analysis_type == "Most Expensive Neighborhoods Rent vs. Sales":
        neighborhood = st.sidebar.selectbox("Enter Neighborhood for Rent vs. Sales Comparison:", neighborhoods, index=neighborhoods.tolist().index("North Beach"))
        st.plotly_chart(most_expensive_neighborhoods_rent_sales(neighborhood))
    elif analysis_type == "Neighborhood Map":
        st.plotly_chart(neighborhood_map())
    elif analysis_type == "Parallel Categories Plot":
        st.plotly_chart(parallel_categories_plot())
    elif analysis_type == "Parallel Coordinates Plot":
        st.plotly_chart(parallel_coordinates_plot())
    elif analysis_type == "Sunburst Plot":
        st.plotly_chart(sunburst_plot())

if __name__ == "__main__":
    main()