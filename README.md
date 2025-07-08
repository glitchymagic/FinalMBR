# FY26 Tech Spot Operational Metrics Dashboard

A comprehensive dashboard for visualizing and analyzing Tech Spot operational metrics based on incident management data and consultation tracking.

## Recent Improvements (July 2025)

- **Robust Date Handling**: Added support for multiple date formats (MM/DD/YYYY, DD/MM/YYYY, YYYY/MM/DD)
- **Timezone Consistency**: Fixed timezone handling to ensure accurate date calculations and filtering
- **Enhanced Drill-downs**: Improved all drill-down functionality for detailed analysis
- **API Completeness**: Added missing API endpoints for comprehensive data access
- **Error Handling**: Improved error handling and reporting throughout the application

## Features

- **Real-time Metrics Dashboard**: Interactive dashboard displaying key operational metrics
- **Trend Analysis**: Monthly trends for incidents, FCR rates, and MTTR
- **Team Performance**: Performance metrics by assignment group
- **Responsive Design**: Modern, dark-themed UI optimized for professional presentations
- **Live Data Updates**: Automatic data refresh every 5 minutes

## Key Metrics Displayed

1. **Incident Data Trends**: Monthly incident volume with change indicators
2. **FCR (First Call Resolution) Rates**: Percentage of incidents resolved on first contact
3. **MTTR (Mean Time To Resolution)**: Average resolution time in hours
4. **Team Performance**: Detailed breakdown by tech spot location
5. **SLA Compliance**: Service level agreement adherence rates

## Setup Instructions

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Data File**:
   Ensure `FY26-6Months.xlsx` is in the project root directory

3. **Start the Application**:
   ```bash
   python app.py
   ```

4. **Access Dashboard**:
   Open your web browser and navigate to: `http://localhost:8080`

## Data Source

The dashboard uses incident management data from `FY26-6Months.xlsx` containing:
- **9,784 incidents** from February 1, 2025 to June 26, 2025
- **Multiple tech spot locations** including DGTC, Homeoffice, JST, Sunnyvale, etc.
- **Comprehensive incident lifecycle data** including creation, resolution, and closure times

## API Endpoints

The Flask backend provides several REST API endpoints:

- `GET /api/overview` - Overview metrics and summary statistics
- `GET /api/trends` - Monthly trend data for charts
- `GET /api/team_performance` - Team-wise performance metrics

## Architecture

- **Backend**: Flask (Python) - Data processing and API endpoints
- **Frontend**: HTML5 + Tailwind CSS + Chart.js - Modern responsive UI
- **Data Processing**: Pandas - Excel file processing and analysis
- **Charts**: Chart.js - Interactive trend visualizations

## Dashboard Sections

### Header Section
- Total technicians, locations, and customers served
- High-level organizational metrics

### Trends Section
- **Incident Data**: Line chart showing monthly incident volume
- **FCR Data**: First Call Resolution percentage trends
- **MTTR Data**: Mean Time To Resolution trends

### Insights Section
- Strategic improvement metrics with percentage changes
- Implementation strategies for operational improvements

### Team Performance Table
- Detailed performance metrics by tech spot location
- Sortable data including incident count, resolution time, and FCR rates

## Data Calculations

- **FCR Rate**: Calculated as incidents with reopen_count = 0
- **MTTR**: Average resolution time converted from minutes to hours
- **SLA Compliance**: Percentage of incidents meeting SLA requirements
- **Monthly Trends**: Time-series analysis of key metrics

## Customization

### Adding New Metrics
1. Update the data processing functions in `app.py`
2. Add new API endpoints as needed
3. Modify the frontend JavaScript to consume new data
4. Update chart configurations in `templates/dashboard.html`

### Styling Changes
- Modify CSS classes in the `<style>` section of `dashboard.html`
- Update Tailwind CSS classes for layout changes
- Customize Chart.js configurations for chart appearance

## Troubleshooting

### Common Issues

1. **Data Not Loading**:
   - Verify `FY26-6Months.xlsx` exists in the project directory
   - Check file permissions
   - Review console logs for error messages

2. **Charts Not Displaying**:
   - Ensure Chart.js CDN is accessible
   - Check browser console for JavaScript errors
   - Verify API endpoints are returning data

3. **Performance Issues**:
   - For large datasets, consider implementing data pagination
   - Add caching mechanisms for frequently accessed data
   - Optimize Excel file reading operations

## Future Enhancements

- Real-time data integration with live incident management systems
- Additional visualization types (bar charts, pie charts, heatmaps)
- Export functionality for reports and presentations
- User authentication and role-based access control
- Historical data comparison and forecasting

## Support

For technical support or feature requests, please contact the development team or create an issue in the project repository.

---

*This dashboard is designed to provide actionable insights for operational improvement and strategic decision-making in Tech Spot operations.* 