import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import numpy as np
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

st.set_page_config(
    page_title="eBanguka Emergency Analytics Dashboard",
    layout="wide"
)

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_data():
    """Load and preprocess the emergency transfer data from API"""
    try:
        # Make request without SSL verification
        with st.spinner('Fetching latest data from eBanguka API...'):
            response = requests.get('https://ebanguka.moh.gov.rw/api/exposed/transfers', 
                                   verify=False, timeout=30)
        
        if response.status_code == 200:
            # Convert JSON response to DataFrame
            data = response.json()
            df = pd.DataFrame(data)
            
            # Convert dict/object columns to JSON strings
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check if any values are dicts
                    sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if isinstance(sample_value, dict):
                        df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
            
            # Convert date columns
            date_columns = ['createdAt', 'updatedAt', 'admissionDate', 'transferDecisionDate']
            for col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Clean and prepare data
            df['age'] = pd.to_numeric(df['age'], errors='coerce')
            df['transfer_hour'] = df['createdAt'].dt.hour
            df['transfer_day_of_week'] = df['createdAt'].dt.day_name()
            df['transfer_month'] = df['createdAt'].dt.strftime('%Y-%m')
            
            # Create time periods
            def get_time_period(hour):
                if pd.isna(hour):
                    return 'Unknown'
                if 6 <= hour < 12:
                    return 'Morning (6AM-12PM)'
                elif 12 <= hour < 18:
                    return 'Afternoon (12PM-6PM)'
                elif 18 <= hour < 24:
                    return 'Evening (6PM-12AM)'
                else:
                    return 'Night (12AM-6AM)'
            
            df['time_period'] = df['transfer_hour'].apply(get_time_period)
            
            # Extract facility names from JSON strings
            df['origin_facility_name'] = df['originFacility'].apply(extract_facility_name)
            df['receiving_facility_name'] = df['receivingFacility'].apply(extract_facility_name)
            
            return df
        else:
            st.error(f"Failed to fetch data: HTTP {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

def extract_facility_name(facility_json):
    """Extract facility name from JSON string"""
    try:
        if pd.isna(facility_json) or facility_json == '{}':
            return 'Unknown'
        facility_data = json.loads(facility_json)
        return facility_data.get('name', 'Unknown')
    except:
        return 'Unknown'

def main():
    st.title("eBanguka Emergency Analytics Dashboard")
    st.markdown("---")
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.error("Unable to load data. Please try again later.")
        return
    
    # Display last updated time
    st.info(f"📊 Data last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} | Total records: {len(df)}")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    if not df['createdAt'].isna().all():
        min_date = df['createdAt'].min().date()
        max_date = df['createdAt'].max().date()
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    else:
        date_range = None
    
    # Province filter
    provinces = ['All'] + sorted(df['province'].dropna().unique().tolist())
    selected_province = st.sidebar.selectbox("Province", provinces)
    
    # Transfer type filter
    transfer_types = ['All'] + sorted(df['transferType'].dropna().unique().tolist())
    selected_transfer_type = st.sidebar.selectbox("Transfer Type", transfer_types)
    
    # Apply filters
    filtered_df = df.copy()
    if date_range and len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['createdAt'].dt.date >= date_range[0]) & 
            (filtered_df['createdAt'].dt.date <= date_range[1])
        ]
    
    if selected_province != 'All':
        filtered_df = filtered_df[filtered_df['province'] == selected_province]
        
    if selected_transfer_type != 'All':
        filtered_df = filtered_df[filtered_df['transferType'] == selected_transfer_type]
    
    # Key Metrics Row
    st.header("Key Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Transfers", len(filtered_df))
    
    with col2:
        emergency_count = len(filtered_df[filtered_df['transferType'] == 'EMERGENCY'])
        st.metric("Emergency Transfers", emergency_count)
    
    with col3:
        non_emergency_count = len(filtered_df[filtered_df['transferType'] == 'NON_EMERGENCY'])
        st.metric("Non Emergency Transfers", non_emergency_count)
    
    with col4:
        follow_up_count = len(filtered_df[filtered_df['transferType'] == 'FOLLOW_UP'])
        st.metric("Follow Up Transfers", follow_up_count)
    
    with col5:
        unknown_transfers = len(filtered_df[filtered_df['transferType'].isnull()])
        st.metric("Unknown Type", unknown_transfers)
    
    with col6:
        secondary_transfers = len(filtered_df[filtered_df['isSecondaryTransfer'] == True])
        st.metric("Secondary Transfers", secondary_transfers)
    
    st.markdown("---")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Transfers by Type")
        transfer_type_counts = filtered_df['transferType'].value_counts()
        if len(transfer_type_counts) > 0:
            fig = px.pie(
                values=transfer_type_counts.values,
                names=transfer_type_counts.index,
                title="Distribution of Transfer Types",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Transfers by Province")
        province_counts = filtered_df['province'].value_counts()
        if len(province_counts) > 0:
            fig = px.bar(
                x=province_counts.index,
                y=province_counts.values,
                title="Emergency Transfers by Province",
                labels={'x': 'Province', 'y': 'Number of Transfers'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Charts Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Transfers by Time Period")
        time_period_transfers = filtered_df['time_period'].value_counts().sort_values(ascending=True)
        if len(time_period_transfers) > 0:
            fig = px.bar(
                x=time_period_transfers.values,
                y=time_period_transfers.index,
                orientation='h',
                title="Transfer Volume by Time Period",
                labels={'x': 'Number of Transfers', 'y': 'Time Period'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Transfers by Day of Week")
        daily_transfers = filtered_df['transfer_day_of_week'].value_counts()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_transfers = daily_transfers.reindex(day_order, fill_value=0)
        if len(daily_transfers) > 0:
            fig = px.bar(
                x=daily_transfers.index,
                y=daily_transfers.values,
                title="Transfer Volume by Day of Week",
                labels={'x': 'Day of Week', 'y': 'Number of Transfers'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Charts Row 3
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Age Distribution")
        age_data = filtered_df['age'].dropna()
        if len(age_data) > 0:
            fig = px.histogram(
                age_data,
                nbins=20,
                title="Patient Age Distribution",
                labels={'value': 'Age', 'count': 'Number of Patients'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No age data available")
    
    with col2:
        st.subheader("Transportation Methods")
        transport_counts = filtered_df['transportationType'].value_counts().head(10).sort_values(ascending=True)
        if len(transport_counts) > 0:
            fig = px.bar(
                x=transport_counts.values,
                y=transport_counts.index,
                orientation='h',
                title="Most Common Transportation Methods",
                labels={'x': 'Number of Transfers', 'y': 'Transportation Type'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No transportation data available")
    
    # Top facilities analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Referring Facilities")
        top_origins = filtered_df['origin_facility_name'].value_counts().head(10).sort_values(ascending=True)
        if len(top_origins) > 0:
            fig = px.bar(
                x=top_origins.values,
                y=top_origins.index,
                orientation='h',
                title="Top 10 Referring Facilities",
                labels={'x': 'Number of Transfers', 'y': 'Facility Name'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No facility data available")
    
    with col2:
        st.subheader("Top Receiving Facilities")
        top_destinations = filtered_df['receiving_facility_name'].value_counts().head(10).sort_values(ascending=True)
        if len(top_destinations) > 0:
            fig = px.bar(
                x=top_destinations.values,
                y=top_destinations.index,
                orientation='h',
                title="Top 10 Receiving Facilities",
                labels={'x': 'Number of Transfers', 'y': 'Facility Name'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No facility data available")
    
    # Transfer reasons analysis
    st.subheader("Top Transfer Reasons")
    reason_counts = filtered_df['transferReason'].value_counts().head(15).sort_values(ascending=True)
    if len(reason_counts) > 0:
        fig = px.bar(
            x=reason_counts.values,
            y=reason_counts.index,
            orientation='h',
            title="Top 15 Transfer Reasons",
            labels={'x': 'Number of Transfers', 'y': 'Transfer Reason'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.subheader("Recent Transfer Data")
    display_columns = [
        'caseCode', 'createdAt', 'transferType', 'gender', 'age', 
        'province', 'district', 'origin_facility_name', 'receiving_facility_name',
        'transferReason', 'transportationType'
    ]
    
    available_columns = [col for col in display_columns if col in filtered_df.columns]
    recent_transfers = filtered_df[available_columns].sort_values('createdAt', ascending=False).head(20)
    
    st.dataframe(
        recent_transfers,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary statistics
    st.subheader("Summary Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Transfer Type Distribution:**")
        transfer_stats = filtered_df['transferType'].value_counts()
        for transfer_type, count in transfer_stats.items():
            percentage = (count / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
            st.write(f"- {transfer_type}: {count} ({percentage:.1f}%)")
    
    with col2:
        st.write("**Gender Distribution:**")
        gender_stats = filtered_df['gender'].value_counts()
        for gender, count in gender_stats.items():
            percentage = (count / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
            st.write(f"- {gender}: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    main()