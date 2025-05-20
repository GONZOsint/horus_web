from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.participant import bp
from app.models import Team, Case, User, FlagSubmission
from app.participant.forms import CreateTeamForm, JoinTeamForm, FlagSubmissionForm
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime
from sqlalchemy import func

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_judge:
        return redirect(url_for('judge.dashboard'))
    
    form = UpdateProfileForm()
    form.username.data = current_user.username
    
    if not current_user.current_team:
        return render_template('participant/dashboard.html', team=None, cases=None, form=form)
    
    # Obtener casos activos solo si el usuario pertenece a un equipo
    cases = Case.query.filter_by(is_active=True, is_found=False).all()
    return render_template('participant/dashboard.html', team=current_user.current_team, cases=cases, form=form)

@bp.route('/cases')
@login_required
def cases():
    if current_user.is_judge:
        return redirect(url_for('judge.dashboard'))
    
    if not current_user.current_team:
        flash('Debes pertenecer a un equipo para ver los casos activos.', 'warning')
        return redirect(url_for('participant.dashboard'))
    
    # Obtener casos activos
    cases = Case.query.filter_by(is_active=True, is_found=False).all()
    
    # Obtener estadísticas de flags para cada caso
    case_stats = {}
    for case in cases:
        # Flags del equipo actual para este caso
        team_flags = FlagSubmission.query.filter_by(
            case_id=case.id,
            team_id=current_user.current_team_id
        ).count()
        
        # Flags aceptadas del equipo actual
        accepted_flags = FlagSubmission.query.filter_by(
            case_id=case.id,
            team_id=current_user.current_team_id,
            is_correct=True
        ).count()
        
        # Flags rechazadas del equipo actual
        rejected_flags = FlagSubmission.query.filter_by(
            case_id=case.id,
            team_id=current_user.current_team_id,
            is_correct=False
        ).count()
        
        # Flags pendientes del equipo actual
        pending_flags = FlagSubmission.query.filter_by(
            case_id=case.id,
            team_id=current_user.current_team_id,
            is_correct=None
        ).count()
        
        case_stats[case.id] = {
            'team_flags': team_flags,
            'accepted_flags': accepted_flags,
            'rejected_flags': rejected_flags,
            'pending_flags': pending_flags
        }
    
    # Create form for flag submission
    form = FlagSubmissionForm()
    
    return render_template('participant/cases.html', cases=cases, case_stats=case_stats, form=form)

@bp.route('/cases/<int:case_id>')
@login_required
def view_case(case_id):
    if current_user.is_judge:
        return redirect(url_for('judge.dashboard'))
    
    if not current_user.current_team:
        flash('Debes pertenecer a un equipo para ver los detalles de los casos.', 'warning')
        return redirect(url_for('participant.dashboard'))
    
    case = Case.query.get_or_404(case_id)
    if not case.is_active or case.is_found:
        flash('Este caso no está disponible.', 'error')
        return redirect(url_for('participant.dashboard'))
    
    form = FlagSubmissionForm()
    return render_template('participant/case_details.html', case=case, form=form)

@bp.route('/cases/<int:case_id>/submit-flag', methods=['POST'])
@login_required
def submit_flag(case_id):
    case = Case.query.get_or_404(case_id)
    if not current_user.is_participant():
        flash('No tienes permiso para enviar flags.', 'error')
        return redirect(url_for('main.index'))
    
    if not current_user.current_team:
        flash('Debes pertenecer a un equipo para enviar flags.', 'warning')
        return redirect(url_for('participant.dashboard'))
    
    form = FlagSubmissionForm()
    if form.validate_on_submit():
        photo_path = None
        if form.photo.data:
            photo = form.photo.data
            filename = secure_filename(f"{case_id}_{current_user.id}_{photo.filename}")
            photo_path = f"uploads/flags/{filename}"
            full_path = os.path.join(current_app.root_path, 'static', 'uploads', 'flags', filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            photo.save(full_path)
        
        # Get points from category
        category_info = FlagSubmission.CATEGORIES.get(form.category.data)
        if not category_info:
            flash('Categoría inválida.', 'error')
            return redirect(url_for('participant.view_case', case_id=case_id))
        
        flag = FlagSubmission(
            case_id=case_id,
            team_id=current_user.current_team_id,
            flag=form.flag.data,
            notes=form.description.data,
            category=form.category.data,
            points=category_info[1],
            source_url=form.source_url.data,
            photo_path=photo_path
        )
        db.session.add(flag)
        db.session.commit()
        flash('Flag enviada exitosamente.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')
    
    return redirect(url_for('participant.view_case', case_id=case_id))

@bp.route('/team/create', methods=['GET', 'POST'])
@login_required
def create_team():
    if current_user.is_judge:
        flash('Los jueces no pueden crear equipos.', 'error')
        return redirect(url_for('judge.dashboard'))
    
    if current_user.current_team:
        flash('Ya perteneces a un equipo. Debes dejar el equipo actual antes de crear uno nuevo.', 'warning')
        return redirect(url_for('participant.dashboard'))
    
    form = CreateTeamForm()
    if form.validate_on_submit():
        team = Team(name=form.name.data, created_by=current_user.id)
        db.session.add(team)
        current_user.current_team = team
        current_user.teams.append(team)
        db.session.commit()
        flash(f'¡Equipo creado exitosamente! Código de invitación: {team.invitation_code}', 'success')
        return redirect(url_for('participant.dashboard'))
    
    return render_template('participant/create_team.html', form=form)

@bp.route('/team/join', methods=['GET', 'POST'])
@login_required
def join_team():
    if current_user.is_judge:
        flash('Los jueces no pueden unirse a equipos.', 'error')
        return redirect(url_for('judge.dashboard'))
    
    if current_user.current_team:
        flash('Ya perteneces a un equipo. Debes dejar el equipo actual antes de unirte a otro.', 'warning')
        return redirect(url_for('participant.dashboard'))
    
    form = JoinTeamForm()
    if form.validate_on_submit():
        team = Team.query.filter_by(invitation_code=form.invitation_code.data.upper()).first()
        if team:
            current_user.current_team = team
            current_user.teams.append(team)
            db.session.commit()
            flash('¡Te has unido al equipo exitosamente!', 'success')
            return redirect(url_for('participant.dashboard'))
        else:
            flash('Código de invitación inválido.', 'error')
    
    return render_template('participant/join_team.html', form=form)

@bp.route('/team/leave')
@login_required
def leave_team():
    if current_user.is_judge:
        flash('Los jueces no pueden dejar equipos.', 'error')
        return redirect(url_for('judge.dashboard'))
    
    if not current_user.current_team:
        flash('No perteneces a ningún equipo.', 'warning')
        return redirect(url_for('participant.dashboard'))
    
    current_user.current_team = None
    db.session.commit()
    flash('Has dejado el equipo.', 'info')
    return redirect(url_for('participant.dashboard'))

@bp.route('/update-profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if current_user.is_judge:
        return redirect(url_for('judge.dashboard'))
    
    form = UpdateProfileForm()
    if form.validate_on_submit():
        # Check if username is already taken by another user
        existing_user = User.query.filter(User.username == form.username.data, User.id != current_user.id).first()
        if existing_user:
            flash('Username is already taken', 'danger')
            return redirect(url_for('participant.dashboard'))
        
        current_user.username = form.username.data
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('participant.dashboard'))
    
    # Pre-populate form with current username
    form.username.data = current_user.username
    return render_template('participant/update_profile.html', form=form)

@bp.route('/fix-photo-paths')
@login_required
def fix_photo_paths():
    if not current_user.is_admin:
        flash('No tienes permiso para realizar esta acción.', 'error')
        return redirect(url_for('main.index'))
    
    submissions = FlagSubmission.query.filter(FlagSubmission.photo_path.isnot(None)).all()
    fixed_count = 0
    
    for submission in submissions:
        print(f"Ruta actual: {submission.photo_path}")  # Debug
        if '\\' in submission.photo_path:
            # Convertir backslashes a forward slashes
            submission.photo_path = submission.photo_path.replace('\\', '/')
            print(f"Ruta corregida: {submission.photo_path}")  # Debug
            fixed_count += 1
    
    if fixed_count > 0:
        db.session.commit()
        flash(f'Se corrigieron {fixed_count} rutas de fotos.', 'success')
    else:
        flash('No se encontraron rutas que necesiten corrección.', 'info')
    
    return redirect(url_for('main.index'))

@bp.route('/team/flags')
@login_required
def team_flags():
    if current_user.is_judge:
        return redirect(url_for('judge.dashboard'))
    
    if not current_user.current_team:
        flash('Debes pertenecer a un equipo para ver las flags.', 'warning')
        return redirect(url_for('participant.dashboard'))
    
    # Obtener todas las flags del equipo actual
    flags = FlagSubmission.query.filter_by(team_id=current_user.current_team_id).order_by(FlagSubmission.submitted_at.desc()).all()
    
    return render_template('participant/team_flags.html', flags=flags) 