import streamlit as st
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load Data
@st.cache_data
def load_data():
    file_path = Path("Data/sfo_neighborhoods_census_data.csv")
    data = pd.read_csv(file_path, index_col="year")
    return data

sfo_data = load_data()

# Get unique neighborhoods for the dropdown
neighborhoods = sfo_data['neighborhood'].unique()

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

# Start Streamlit App
def main():
    st.title("San Francisco Housing Cost Analysis Dashboard")
    st.sidebar.title("Options")

    analysis_type = st.sidebar.radio(
        "Choose the Analysis Type:",
        ("Housing Units Per Year", "Average Gross Rent", "Average Sales Price", 
         "Average Price by Neighborhood", "Top 10 Most Expensive Neighborhoods", 
         "Most Expensive Neighborhoods Rent vs. Sales")
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

if __name__ == "__main__":
    main()