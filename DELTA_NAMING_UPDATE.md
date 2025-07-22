# Delta Naming Update Summary

## Changes Made

Updated the three main chart card titles in the dashboard to include "Delta Δ" instead of "Data":

### Before:
- Incident Data
- MTTR Data  
- FCR Data

### After:
- Incident Delta Δ
- MTTR Delta Δ
- FCR Delta Δ

## Files Modified:
- `templates/dashboard.html`
  - Updated H3 titles for all three cards
  - Updated HTML comments to match

## Visual Impact:
The delta symbol (Δ) adds a more analytical/mathematical feel to the dashboard, suggesting change measurement and trend analysis rather than just static data display.

## Note:
The delta symbol (Δ) is commonly used in analytics to represent:
- Change over time
- Difference between values
- Rate of change
- Variance analysis

This naming convention better reflects that these charts show trends and changes over the 6-month period. 