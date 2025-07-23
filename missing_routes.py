# CRITICAL DRILL-DOWN API ROUTES - RESTORED FOR INCIDENTS TAB
@app.route('/api/mttr_drill_down')
def api_mttr_drill_down():
    """MTTR drill-down API for monthly incident resolution time analysis"""
    try:
        month = request.args.get('month', 'all')
        location = request.args.get('location', 'all')
        region = request.args.get('region', 'all')
        assignment_group = request.args.get('assignment_group', 'all')
        
        # Apply filters to get filtered incidents
        filtered_df = apply_filters(incidents_df, 'all', month, location, region, assignment_group)
        
        if filtered_df.empty:
            return jsonify({
                'incidents': [],
                'total_incidents': 0,
                'avg_mttr_hours': 0,
                'filter_context': {'month': month, 'location': location, 'region': region, 'assignment_group': assignment_group}
            })
        
        # Calculate MTTR for each incident
        incidents_list = []
        for _, incident in filtered_df.iterrows():
            try:
                opened = pd.to_datetime(incident['Opened'])
                resolved = pd.to_datetime(incident['Resolved'])
                mttr_hours = (resolved - opened).total_seconds() / 3600
                
                incidents_list.append({
                    'number': str(incident['Number']),
                    'short_description': str(incident['Short description'])[:50],
                    'opened': opened.strftime('%Y-%m-%d %H:%M'),
                    'resolved': resolved.strftime('%Y-%m-%d %H:%M'),
                    'mttr_hours': round(mttr_hours, 2),
                    'resolved_by': str(incident['Resolved by']),
                    'assignment_group': str(incident['Assignment group'])
                })
            except Exception as e:
                continue
        
        # Calculate average MTTR
        total_mttr = sum(inc['mttr_hours'] for inc in incidents_list)
        avg_mttr = total_mttr / len(incidents_list) if incidents_list else 0
        
        return jsonify({
            'incidents': incidents_list,
            'total_incidents': len(incidents_list),
            'avg_mttr_hours': round(avg_mttr, 2),
            'filter_context': {'month': month, 'location': location, 'region': region, 'assignment_group': assignment_group}
        })
        
    except Exception as e:
        return jsonify({'error': f'MTTR drill-down error: {str(e)}'}), 500

@app.route('/api/incident_drill_down')
def api_incident_drill_down():
    """Incident drill-down API for monthly incident details"""
    try:
        month = request.args.get('month', 'all')
        location = request.args.get('location', 'all')
        region = request.args.get('region', 'all')
        assignment_group = request.args.get('assignment_group', 'all')
        
        # Apply filters to get filtered incidents
        filtered_df = apply_filters(incidents_df, 'all', month, location, region, assignment_group)
        
        if filtered_df.empty:
            return jsonify({
                'incidents': [],
                'total_incidents': 0,
                'filter_context': {'month': month, 'location': location, 'region': region, 'assignment_group': assignment_group}
            })
        
        # Get incident details
        incidents_list = []
        for _, incident in filtered_df.iterrows():
            try:
                incidents_list.append({
                    'number': str(incident['Number']),
                    'short_description': str(incident['Short description'])[:50],
                    'opened': pd.to_datetime(incident['Opened']).strftime('%Y-%m-%d %H:%M'),
                    'resolved': pd.to_datetime(incident['Resolved']).strftime('%Y-%m-%d %H:%M') if pd.notna(incident['Resolved']) else 'Not Resolved',
                    'state': str(incident['State']),
                    'priority': str(incident['Priority']),
                    'resolved_by': str(incident['Resolved by']),
                    'assignment_group': str(incident['Assignment group'])
                })
            except Exception as e:
                continue
        
        return jsonify({
            'incidents': incidents_list,
            'total_incidents': len(incidents_list),
            'filter_context': {'month': month, 'location': location, 'region': region, 'assignment_group': assignment_group}
        })
        
    except Exception as e:
        return jsonify({'error': f'Incident drill-down error: {str(e)}'}), 500

@app.route('/api/fcr_drill_down')
def api_fcr_drill_down():
    """FCR drill-down API for first call resolution analysis"""
    try:
        month = request.args.get('month', 'all')
        location = request.args.get('location', 'all')
        region = request.args.get('region', 'all')
        assignment_group = request.args.get('assignment_group', 'all')
        
        # Apply filters to get filtered incidents
        filtered_df = apply_filters(incidents_df, 'all', month, location, region, assignment_group)
        
        if filtered_df.empty:
            return jsonify({
                'incidents': [],
                'total_incidents': 0,
                'fcr_count': 0,
                'fcr_rate': 0,
                'filter_context': {'month': month, 'location': location, 'region': region, 'assignment_group': assignment_group}
            })
        
        # Calculate FCR for each incident
        incidents_list = []
        fcr_count = 0
        
        for _, incident in filtered_df.iterrows():
            try:
                # FCR logic: incidents with 0 or 1 reassignments
                reassignment_count = incident.get('Reassignment count', 0)
                is_fcr = reassignment_count <= 1
                
                if is_fcr:
                    fcr_count += 1
                
                incidents_list.append({
                    'number': str(incident['Number']),
                    'short_description': str(incident['Short description'])[:50],
                    'opened': pd.to_datetime(incident['Opened']).strftime('%Y-%m-%d %H:%M'),
                    'resolved': pd.to_datetime(incident['Resolved']).strftime('%Y-%m-%d %H:%M') if pd.notna(incident['Resolved']) else 'Not Resolved',
                    'reassignment_count': int(reassignment_count) if pd.notna(reassignment_count) else 0,
                    'is_fcr': is_fcr,
                    'resolved_by': str(incident['Resolved by']),
                    'assignment_group': str(incident['Assignment group'])
                })
            except Exception as e:
                continue
        
        # Calculate FCR rate
        fcr_rate = (fcr_count / len(incidents_list)) * 100 if incidents_list else 0
        
        return jsonify({
            'incidents': incidents_list,
            'total_incidents': len(incidents_list),
            'fcr_count': fcr_count,
            'fcr_rate': round(fcr_rate, 1),
            'filter_context': {'month': month, 'location': location, 'region': region, 'assignment_group': assignment_group}
        })
        
    except Exception as e:
        return jsonify({'error': f'FCR drill-down error: {str(e)}'}), 500
