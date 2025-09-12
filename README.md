# eBanguka Emergency Analytics Dashboard

A real-time analytics dashboard for Rwanda's eBanguka emergency transfer system, providing insights into patient transfers across healthcare facilities.

## Features

- **Real-time Data**: Fetches latest transfer data from eBanguka API
- **Interactive Visualizations**: Charts showing transfer patterns, facility usage, and patient demographics
- **Filtering Options**: Filter by date range, province, and transfer type
- **Key Metrics**: Emergency transfers, patient demographics, facility statistics
- **Time Analysis**: Transfer patterns by time of day and day of week

## Live Dashboard

🚀 **[View Live Dashboard](https://your-streamlit-app-url.streamlit.app)**

## Data Sources

- **API**: eBanguka Ministry of Health Rwanda
- **Update Frequency**: Data refreshed every 30 minutes
- **Coverage**: All emergency transfers across Rwanda healthcare facilities

## Technical Stack

- **Framework**: Streamlit
- **Visualization**: Plotly
- **Data Processing**: Pandas
- **Deployment**: Streamlit Cloud

## Local Development

```bash
# Clone repository
git clone https://github.com/your-username/ebanguka-dashboard.git

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run app.py
```

## Dashboard Sections

1. **Key Metrics** - Overview of transfer statistics
2. **Transfer Types** - Distribution of emergency vs non-emergency transfers
3. **Geographic Analysis** - Transfers by province and facilities
4. **Time Patterns** - Transfer volumes by time period and day
5. **Patient Demographics** - Age and gender distributions
6. **Facility Analytics** - Top referring and receiving facilities
7. **Transfer Reasons** - Most common reasons for patient transfers

## Data Privacy

- Patient personal information is anonymized in the API
- Only aggregated statistics and trends are displayed
- No individual patient records are exposed

## Contact

For questions about the eBanguka system or this dashboard, contact the NHIC team.