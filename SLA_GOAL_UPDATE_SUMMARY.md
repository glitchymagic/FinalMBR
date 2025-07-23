# SLA Goal Update Summary

## Change Overview
Updated the SLA Goal threshold from **3 hours (180 minutes)** to **3 hours 12 minutes (192 minutes)**.

## Files Modified

### 1. app.py
- **Line 66**: Updated `SLA_GOAL_MINUTES` constant from 180 to 192
  ```python
  SLA_GOAL_MINUTES = 192       # Goal SLA: 3 hours 12 minutes (192 minutes)
  ```
- **Line 107**: Updated print statement to reflect new 192-min goal
- **Line 336**: Updated comment to reflect new goal threshold

### 2. templates/dashboard.html
- **SLA Chart Target Line**: 
  - Changed `yMin` and `yMax` from 180 to 192
  - Updated label from "Target (3hrs)" to "Target (3hrs 12min)"
- **Dashboard Subtitle**: Updated SLA subtitle to show "Goal: 3hrs 12min | Baseline: 4hrs"

## Impact on Metrics

### Before (180-minute goal):
- SLA Goal Compliance: **95.3%**
- 9,853 out of 10,342 incidents met the 3-hour goal

### After (192-minute goal):
- SLA Goal Compliance: **95.6%**
- 9,885 out of 10,342 incidents meet the 3-hour-12-minute goal
- **32 additional incidents** now meet the relaxed goal threshold

## Dashboard Visualization
- The green dashed target line in the SLA Compliance chart now appears at 192 minutes (3.2 hours)
- The candlestick chart will show more green bars (meeting goal) as the threshold is higher
- Team performance table continues to show goal compliance percentages with the new threshold

## Notes
- The baseline SLA remains unchanged at 4 hours (240 minutes)
- The SLA breach calculation remains based on the 4-hour baseline
- This change reflects a more achievable goal while maintaining the same service baseline
- All historical data has been recalculated with the new goal threshold 