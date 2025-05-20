from flask import render_template, jsonify, request
from flask_login import current_user
from app.main import bp
from ..models import Team, FlagSubmission
from datetime import datetime, timedelta
from sqlalchemy import func
import json

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html')

@bp.route('/scoreboard')
def scoreboard():
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of teams per page
    
    # Get all teams ordered by points
    teams = Team.query.order_by(Team.points.desc()).paginate(page=page, per_page=per_page)
    
    # Get top 10 teams for the chart
    top_teams = Team.query.order_by(Team.points.desc()).limit(10).all()
    top_teams_labels = [team.name for team in top_teams]
    top_teams_points = [team.points for team in top_teams]
    
    print("Debug - Top Teams Data:")
    print(f"Labels: {top_teams_labels}")
    print(f"Points: {top_teams_points}")
    
    # Get points over time data
    # Get submissions from the last 7 days
    start_date = datetime.utcnow() - timedelta(days=7)
    submissions = FlagSubmission.query.filter(
        FlagSubmission.submitted_at >= start_date
    ).order_by(FlagSubmission.submitted_at).all()
    
    # Create time series data for each team
    time_labels = []
    time_series_data = []
    
    # Get unique timestamps
    timestamps = sorted(set(sub.submitted_at.strftime('%Y-%m-%d %H:%M') for sub in submissions))
    time_labels = timestamps
    
    # Calculate cumulative points for each team
    team_points = {}
    for team in Team.query.all():
        team_points[team.id] = 0
        points_over_time = []
        
        for timestamp in timestamps:
            # Get all submissions up to this timestamp
            submissions_up_to_time = [s for s in submissions 
                                    if s.team_id == team.id 
                                    and s.submitted_at.strftime('%Y-%m-%d %H:%M') <= timestamp]
            
            # Calculate total points
            points = sum(sub.points for sub in submissions_up_to_time if sub.is_correct)
            points_over_time.append(points)
        
        # Generate a consistent color for each team
        color_hash = hash(team.name) % 360
        time_series_data.append({
            'label': team.name,
            'data': points_over_time,
            'borderColor': f'hsl({color_hash}, 70%, 50%)',
            'backgroundColor': f'hsla({color_hash}, 70%, 50%, 0.1)',
            'fill': True,
            'tension': 0.4
        })
    
    print("Debug - Time Series Data:")
    print(f"Labels: {time_labels}")
    print(f"Data: {time_series_data}")
    
    return render_template('main/scoreboard.html',
                         teams=teams,
                         top_teams_labels=json.dumps(top_teams_labels),
                         top_teams_points=json.dumps(top_teams_points),
                         time_labels=json.dumps(time_labels),
                         time_series_data=json.dumps(time_series_data)) 