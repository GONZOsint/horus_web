from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.judge import bp
from app import db
from app.models import User, Case, Participant, FlagSubmission
from app.cndes_scraper import scrape_cndes_case
from datetime import datetime
from app.judge.forms import CaseForm
from app.utils import save_case_photo
import os

@bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_judge:
        return redirect(url_for('participant.dashboard'))
    cases = Case.query.filter_by(created_by=current_user.id).order_by(Case.created_at.desc()).all()
    return render_template('judge/dashboard.html', cases=cases)

@bp.route('/cases')
@login_required
def cases():
    if not current_user.is_judge:
        return redirect(url_for('participant.dashboard'))
    cases = Case.query.filter_by(created_by=current_user.id).order_by(Case.created_at.desc()).all()
    return render_template('judge/cases.html', cases=cases)

@bp.route('/cases/new', methods=['GET', 'POST'])
@login_required
def new_case():
    if not current_user.is_judge:
        flash('Acceso denegado. Solo los jueces pueden crear casos.', 'error')
        return redirect(url_for('participant.dashboard'))
    
    form = CaseForm()
    if form.validate_on_submit():
        try:
            # Crear el caso primero para obtener el ID
            case = Case(
                title=form.title.data,
                description=form.description.data,
                disappearance_date=form.disappearance_date.data,
                birth_date=form.birth_date.data,
                age_at_disappearance=form.age_at_disappearance.data,
                current_age=form.current_age.data,
                disappearance_location=form.disappearance_location.data,
                gender=form.gender.data,
                eye_color=form.eye_color.data,
                hair_color=form.hair_color.data,
                hair_type=form.hair_type.data,
                hair_length=form.hair_length.data,
                body_type=form.body_type.data,
                height=form.height.data,
                weight=form.weight.data,
                last_seen_clothing=form.last_seen_clothing.data,
                first_name=form.first_name.data,
                last_name1=form.last_name1.data,
                last_name2=form.last_name2.data,
                disappearance_type=form.disappearance_type.data,
                needs=form.needs.data,
                is_found=request.form.get('is_found') == 'on',
                is_active=request.form.get('is_active') == 'on',
                created_by=current_user.id
            )
            
            # Guardar el caso para obtener el ID
            db.session.add(case)
            db.session.flush()  # Esto genera el ID sin hacer commit
            
            # Procesar la imagen si existe
            if form.photo.data:
                photo_path = save_case_photo(form.photo.data, case.id)
                if photo_path:
                    case.photo_path = photo_path
                else:
                    flash('Error al procesar la imagen. El caso se creará sin foto.', 'warning')
            
            # Hacer commit de todos los cambios
            db.session.commit()
            
            flash('Caso creado exitosamente.', 'success')
            
            # Return JSON response with case ID
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'case_id': case.id,
                    'redirect_url': url_for('judge.cases')
                })
            
            return redirect(url_for('judge.cases'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear caso: {str(e)}")
            flash('Error al crear el caso. Por favor, intente nuevamente.', 'error')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': str(e)}), 500
    
    return render_template('judge/case_form.html', form=form)

@bp.route('/cases/<int:case_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_case(case_id):
    if not current_user.is_judge:
        flash('Acceso denegado. Solo los jueces pueden editar casos.', 'error')
        return redirect(url_for('participant.dashboard'))
    
    case = Case.query.get_or_404(case_id)
    if case.created_by != current_user.id:
        flash('No tienes permiso para editar este caso', 'error')
        return redirect(url_for('judge.cases'))
    
    form = CaseForm(obj=case)  # Poblar el formulario con los datos del caso
    
    if form.validate_on_submit():
        try:
            # Actualizar los campos del caso
            form.populate_obj(case)
            
            # Procesar la imagen si se ha subido una nueva
            if form.photo.data:
                photo_path = save_case_photo(form.photo.data, case.id)
                if photo_path:
                    case.photo_path = photo_path
                else:
                    flash('Error al procesar la imagen. Se mantendrá la imagen anterior.', 'warning')
            
            db.session.commit()
            flash('Caso actualizado exitosamente.', 'success')
            return redirect(url_for('judge.cases'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al actualizar caso: {str(e)}")
            flash('Error al actualizar el caso. Por favor, intente nuevamente.', 'error')
    
    return render_template('judge/case_form.html', form=form, case=case)

@bp.route('/cases/<int:case_id>/delete', methods=['POST'])
@login_required
def delete_case(case_id):
    current_app.logger.info(f"Attempting to delete case {case_id}")
    
    if not current_user.is_judge:
        current_app.logger.warning(f"Non-judge user {current_user.id} attempted to delete case {case_id}")
        flash('Acceso denegado. Solo los jueces pueden eliminar casos.', 'error')
        return redirect(url_for('participant.dashboard'))
    
    try:
        case = Case.query.get_or_404(case_id)
        current_app.logger.info(f"Found case {case_id} created by {case.created_by}")
        
        if case.created_by != current_user.id:
            current_app.logger.warning(f"User {current_user.id} attempted to delete case {case_id} created by {case.created_by}")
            flash('No tienes permiso para eliminar este caso', 'error')
            return redirect(url_for('judge.cases'))
        
        # Delete the case photo if it exists
        if case.photo_path:
            try:
                photo_path = os.path.join(current_app.static_folder, case.photo_path)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                    current_app.logger.info(f"Deleted photo for case {case_id}")
            except Exception as e:
                current_app.logger.error(f"Error deleting case photo: {str(e)}")
        
        db.session.delete(case)
        db.session.commit()
        current_app.logger.info(f"Successfully deleted case {case_id}")
        flash('Caso eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting case {case_id}: {str(e)}")
        flash('Error al eliminar el caso. Por favor, intente nuevamente.', 'error')
    
    return redirect(url_for('judge.cases'))

@bp.route('/import_cndes_case', methods=['POST'])
@login_required
def import_cndes_case():
    if not current_user.is_judge:
        return jsonify({'error': 'Access denied'}), 403
        
    try:
        data = request.get_json()
        if not data or 'cndes_url' not in data:
            return jsonify({'error': 'No CNDES URL provided'}), 400
            
        # Get case data from CNDES
        case_data, success, error_msg = scrape_cndes_case(data.get('cndes_url'))
        if not success:
            return jsonify({'error': error_msg}), 400
            
        # Extract photo data
        photo_data = case_data.get('photo')
        if photo_data:
            # Remove the photo from case_data to reduce response size
            case_data.pop('photo')
            
        # Return the case data and photo separately
        return jsonify({
            'message': 'Case data retrieved successfully',
            'case_data': case_data,
            'photo_data': photo_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error importing case: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/save_case_photo', methods=['POST'])
@login_required
def save_case_photo_route():
    if not current_user.is_judge:
        return jsonify({'error': 'Access denied'}), 403
        
    try:
        data = request.get_json()
        current_app.logger.info(f"Received photo save request: {bool(data)}")
        
        if not data or 'photo_data' not in data or 'case_id' not in data:
            current_app.logger.error("Missing required data in photo save request")
            return jsonify({'error': 'Missing required data'}), 400
            
        case_id = int(data['case_id'])
        photo_data = data['photo_data']
        
        current_app.logger.info(f"Attempting to save photo for case {case_id}")
        current_app.logger.debug(f"Photo data type: {type(photo_data)}")
        
        photo_path = save_case_photo(photo_data, case_id)
        
        if not photo_path:
            current_app.logger.error("Failed to save photo")
            return jsonify({'error': 'Failed to save photo'}), 500
            
        # Update the case with the photo path
        case = Case.query.get(case_id)
        if case:
            case.photo_path = photo_path
            db.session.commit()
            current_app.logger.info(f"Successfully saved photo at {photo_path}")
        else:
            current_app.logger.error(f"Case {case_id} not found")
            return jsonify({'error': 'Case not found'}), 404
            
        return jsonify({
            'message': 'Photo saved successfully',
            'photo_path': photo_path
        })
        
    except Exception as e:
        current_app.logger.error(f"Error saving photo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    if not current_user.is_judge:
        return redirect(url_for('participant.dashboard'))
    
    username = request.form.get('username')
    
    if not username:
        flash('Username is required', 'danger')
        return redirect(url_for('judge.dashboard'))
    
    if len(username) < 3:
        flash('Username must be at least 3 characters long', 'danger')
        return redirect(url_for('judge.dashboard'))
    
    # Check if username is already taken by another user
    existing_user = User.query.filter(User.username == username, User.id != current_user.id).first()
    if existing_user:
        flash('Username is already taken', 'danger')
        return redirect(url_for('judge.dashboard'))
    
    current_user.username = username
    db.session.commit()
    
    flash('Profile updated successfully', 'success')
    return redirect(url_for('judge.dashboard'))

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    if not current_user.is_judge:
        return redirect(url_for('participant.dashboard'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required', 'danger')
        return redirect(url_for('judge.dashboard'))
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('judge.dashboard'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('judge.dashboard'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long', 'danger')
        return redirect(url_for('judge.dashboard'))
    
    # Check password strength
    has_upper = any(c.isupper() for c in new_password)
    has_lower = any(c.islower() for c in new_password)
    has_digit = any(c.isdigit() for c in new_password)
    has_special = any(not c.isalnum() for c in new_password)
    
    if not all([has_upper, has_lower, has_digit, has_special]):
        flash('Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character', 'danger')
        return redirect(url_for('judge.dashboard'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully', 'success')
    return redirect(url_for('judge.dashboard'))

@bp.route('/flag-reviews')
@login_required
def flag_reviews():
    if not current_user.is_judge:
        return redirect(url_for('participant.dashboard'))
    
    # Get all flag submissions that haven't been reviewed yet
    pending_submissions = FlagSubmission.query.filter_by(is_correct=None).order_by(FlagSubmission.submitted_at.desc()).all()
    
    # Get all reviewed submissions
    reviewed_submissions = FlagSubmission.query.filter(FlagSubmission.is_correct.isnot(None)).order_by(FlagSubmission.reviewed_at.desc()).all()
    
    return render_template('judge/flag_reviews.html', 
                         pending_submissions=pending_submissions,
                         reviewed_submissions=reviewed_submissions)

@bp.route('/flag-reviews/<int:submission_id>/review', methods=['POST'])
@login_required
def review_flag(submission_id):
    if not current_user.is_judge:
        return redirect(url_for('participant.dashboard'))
    
    submission = FlagSubmission.query.get_or_404(submission_id)
    
    # Get the review decision from the form
    is_correct = request.form.get('is_correct') == 'true'
    review_notes = request.form.get('review_notes', '')
    
    # Update the submission
    submission.is_correct = is_correct
    submission.reviewed_at = datetime.utcnow()
    submission.reviewed_by = current_user.id
    submission.review_notes = review_notes
    
    # Update team points
    submission.team.update_points()
    
    db.session.commit()
    
    flash('Flag revisada exitosamente.', 'success')
    return redirect(url_for('judge.flag_reviews'))

@bp.route('/check-new-flags')
@login_required
def check_new_flags():
    if not current_user.is_judge:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get the count of pending flags
    pending_count = FlagSubmission.query.filter_by(is_correct=None).count()
    
    return jsonify({
        'has_new_flags': pending_count > 0
    })

@bp.route('/get-flags-status')
@login_required
def get_flags_status():
    if not current_user.is_judge:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get counts of pending and reviewed flags
    pending_count = FlagSubmission.query.filter_by(is_correct=None).count()
    reviewed_count = FlagSubmission.query.filter(FlagSubmission.is_correct.isnot(None)).count()
    
    return jsonify({
        'pending_count': pending_count,
        'reviewed_count': reviewed_count,
        'has_new_pending': pending_count > 0
    })

@bp.route('/get-pending-flags')
@login_required
def get_pending_flags():
    if not current_user.is_judge:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get pending submissions
    pending_submissions = FlagSubmission.query.filter_by(is_correct=None).order_by(FlagSubmission.submitted_at.desc()).all()
    
    # Convert submissions to a list of dictionaries
    submissions_data = []
    for submission in pending_submissions:
        submission_dict = {
            'id': submission.id,
            'case_title': submission.case.title,
            'team_name': submission.team.name,
            'flag': submission.flag,
            'points': submission.points,
            'source_url': submission.source_url,
            'notes': submission.notes,
            'photo_path': submission.photo_path,
            'category_name': submission.category_name,
            'submitted_at': submission.submitted_at.strftime('%d/%m/%Y %H:%M')
        }
        submissions_data.append(submission_dict)
    
    return jsonify({
        'submissions': submissions_data
    }) 