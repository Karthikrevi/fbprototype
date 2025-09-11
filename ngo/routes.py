
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from extensions import db
from fbregistry.models import *
from fbregistry.services import generate_udi, make_qr_png, hash_video, allowed_file, compress_image
from fbregistry.geo import find_nearest_ward, validate_coordinates
from datetime import datetime, date, timedelta
import os
import json

ngo_bp = Blueprint('ngo', __name__)

@ngo_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(
            email=email, 
            role__in=[UserRole.NGO_ADMIN, UserRole.NGO_FIELD]
        ).first()
        
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity=user.id)
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            response = redirect(url_for('ngo.dashboard'))
            set_access_cookies(response, access_token)
            
            flash(f'Welcome back, {user.name}!', 'success')
            return response
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('ngo/login.html')

@ngo_bp.route('/logout')
@jwt_required()
def logout():
    response = redirect(url_for('ngo.login'))
    unset_jwt_cookies(response)
    flash('You have been logged out', 'success')
    return response

@ngo_bp.route('/dashboard')
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role not in [UserRole.NGO_ADMIN, UserRole.NGO_FIELD]:
        flash('Access denied', 'error')
        return redirect(url_for('ngo.login'))
    
    # Dashboard statistics
    stats = {}
    
    # Animals registered by this NGO
    stats['total_animals'] = Animal.query.filter_by(ngo_id=user.ngo_id).count()
    stats['animals_this_month'] = Animal.query.filter(
        Animal.ngo_id == user.ngo_id,
        Animal.created_at >= datetime.now().replace(day=1)
    ).count()
    
    # Vaccinations needing review
    stats['pending_reviews'] = Vaccination.query.join(Animal).filter(
        Animal.ngo_id == user.ngo_id,
        Vaccination.status == VaccinationStatus.PENDING
    ).count()
    
    # Due boosters
    stats['due_boosters'] = Vaccination.query.join(Animal).filter(
        Animal.ngo_id == user.ngo_id,
        Vaccination.next_due <= date.today(),
        Vaccination.status == VaccinationStatus.APPROVED
    ).count()
    
    # Overdue utilizations (if NGO admin)
    stats['overdue_utilizations'] = 0
    if user.role == UserRole.NGO_ADMIN:
        stats['overdue_utilizations'] = DonationUtilization.query.join(Donation).filter(
            Donation.beneficiary_ref == str(user.ngo_id),
            DonationUtilization.status == UtilizationStatus.PENDING,
            DonationUtilization.created_at <= datetime.now() - timedelta(days=7)
        ).count()
    
    # Recent animals
    recent_animals = Animal.query.filter_by(ngo_id=user.ngo_id).order_by(
        Animal.created_at.desc()
    ).limit(5).all()
    
    # Recent vaccinations
    recent_vaccinations = Vaccination.query.join(Animal).filter(
        Animal.ngo_id == user.ngo_id
    ).order_by(Vaccination.date_time.desc()).limit(5).all()
    
    # Pending reviews (for admins)
    pending_reviews = []
    if user.role == UserRole.NGO_ADMIN:
        pending_reviews = Vaccination.query.join(Animal).filter(
            Animal.ngo_id == user.ngo_id,
            Vaccination.status == VaccinationStatus.PENDING
        ).order_by(Vaccination.date_time.desc()).limit(10).all()
    
    return render_template('ngo/dashboard.html', 
                         user=user, 
                         stats=stats,
                         recent_animals=recent_animals,
                         recent_vaccinations=recent_vaccinations,
                         pending_reviews=pending_reviews)

@ngo_bp.route('/animals/new', methods=['GET', 'POST'])
@jwt_required()
def register_animal():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role not in [UserRole.NGO_ADMIN, UserRole.NGO_FIELD]:
        flash('Access denied', 'error')
        return redirect(url_for('ngo.login'))
    
    if request.method == 'POST':
        try:
            # Generate UDI
            udi, short_id = generate_udi()
            
            # Get form data
            animal_data = {
                'udi': udi,
                'short_id': short_id,
                'type': AnimalType.STRAY if request.form.get('type') == 's' else AnimalType.PET,
                'name': request.form.get('name') or None,
                'sex': request.form.get('sex'),
                'color': request.form.get('color'),
                'breed': request.form.get('breed'),
                'approx_age': request.form.get('approx_age'),
                'aggression_marker': AggressionLevel(request.form.get('aggression_marker', 'Friendly')),
                'ngo_id': user.ngo_id,
                'created_by': user.id
            }
            
            # Handle geolocation
            lat = request.form.get('lat', type=float)
            lng = request.form.get('lng', type=float)
            accuracy = request.form.get('accuracy', type=float)
            
            if lat and lng:
                # Validate coordinates
                validation = validate_coordinates(lat, lng, accuracy)
                if not validation['valid']:
                    flash('Invalid GPS coordinates', 'error')
                    return render_template('ngo/register_animal.html', user=user)
                
                animal_data.update({
                    'lat': lat,
                    'lng': lng,
                    'accuracy_m': accuracy
                })
                
                # Find nearest ward
                nearest_ward = find_nearest_ward(lat, lng)
                if nearest_ward:
                    animal_data['ward_id'] = nearest_ward['id']
            
            # Create animal
            animal = Animal(**animal_data)
            db.session.add(animal)
            db.session.commit()
            
            # Generate QR code
            verify_url = url_for('public.verify_udi', udi=udi, _external=True)
            qr_path = os.path.join('static', 'qrcodes', f'{udi}.png')
            
            if make_qr_png(verify_url, qr_path):
                flash(f'Animal registered successfully! UDI: {udi}', 'success')
            else:
                flash(f'Animal registered but QR generation failed. UDI: {udi}', 'warning')
            
            return redirect(url_for('ngo.animal_detail', animal_id=animal.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('ngo/register_animal.html', user=user)

@ngo_bp.route('/animals/<int:animal_id>')
@jwt_required()
def animal_detail(animal_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    animal = Animal.query.filter_by(id=animal_id, ngo_id=user.ngo_id).first()
    if not animal:
        flash('Animal not found', 'error')
        return redirect(url_for('ngo.dashboard'))
    
    # Get vaccination history
    vaccinations = Vaccination.query.filter_by(animal_id=animal.id).order_by(
        Vaccination.date_time.desc()
    ).all()
    
    return render_template('ngo/animal_detail.html', 
                         user=user, 
                         animal=animal, 
                         vaccinations=vaccinations)

@ngo_bp.route('/vaccinations/new')
@jwt_required()
def new_vaccination():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    animal_id = request.args.get('animal_id', type=int)
    animal = None
    
    if animal_id:
        animal = Animal.query.filter_by(id=animal_id, ngo_id=user.ngo_id).first()
        if not animal:
            flash('Animal not found', 'error')
            return redirect(url_for('ngo.dashboard'))
    
    # Get all animals for this NGO
    animals = Animal.query.filter_by(ngo_id=user.ngo_id).order_by(Animal.name).all()
    
    return render_template('ngo/vaccination_form.html', 
                         user=user, 
                         animals=animals, 
                         selected_animal=animal)

@ngo_bp.route('/vaccinations/submit', methods=['POST'])
@jwt_required()
def submit_vaccination():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    try:
        animal_id = request.form.get('animal_id', type=int)
        animal = Animal.query.filter_by(id=animal_id, ngo_id=user.ngo_id).first()
        
        if not animal:
            flash('Animal not found', 'error')
            return redirect(url_for('ngo.dashboard'))
        
        # Create vaccination record
        vaccination = Vaccination(
            animal_id=animal.id,
            type=request.form.get('vaccine_type'),
            brand=request.form.get('brand'),
            batch=request.form.get('batch'),
            expiry=datetime.strptime(request.form.get('expiry'), '%Y-%m-%d').date(),
            dose_ml=float(request.form.get('dose_ml')),
            route=request.form.get('route'),
            site=request.form.get('site'),
            date_time=datetime.strptime(request.form.get('date_time'), '%Y-%m-%dT%H:%M'),
            mode=VaccinationMode.OUTDOOR,
            verifier_id=user.id,
            status=VaccinationStatus.PENDING
        )
        
        # Calculate next due date
        if request.form.get('next_due'):
            vaccination.next_due = datetime.strptime(request.form.get('next_due'), '%Y-%m-%d').date()
        
        # Handle geolocation
        lat = request.form.get('lat', type=float)
        lng = request.form.get('lng', type=float)
        accuracy = request.form.get('accuracy', type=float)
        
        if lat and lng:
            vaccination.lat = lat
            vaccination.lng = lng
            vaccination.accuracy_m = accuracy
        
        # Handle video upload
        if 'video_proof' in request.files:
            video_file = request.files['video_proof']
            if video_file and video_file.filename and allowed_file(video_file.filename, {'mp4'}):
                filename = secure_filename(f"{animal.udi}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                video_path = os.path.join(current_app.config['UPLOAD_DIR'], 'videos', filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(video_path), exist_ok=True)
                
                video_file.save(video_path)
                
                # Calculate hash
                video_hash = hash_video(video_path)
                
                vaccination.video_url = f"/uploads/videos/{filename}"
                vaccination.video_sha256 = video_hash
        
        db.session.add(vaccination)
        db.session.commit()
        
        flash('Vaccination submitted for review', 'success')
        return redirect(url_for('ngo.animal_detail', animal_id=animal.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Vaccination submission failed: {str(e)}', 'error')
        return redirect(url_for('ngo.new_vaccination'))

@ngo_bp.route('/review/queue')
@jwt_required()
def review_queue():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != UserRole.NGO_ADMIN:
        flash('Access denied - Admin only', 'error')
        return redirect(url_for('ngo.dashboard'))
    
    # Get pending vaccinations for this NGO
    pending_vaccinations = Vaccination.query.join(Animal).filter(
        Animal.ngo_id == user.ngo_id,
        Vaccination.status == VaccinationStatus.PENDING
    ).order_by(Vaccination.date_time.desc()).all()
    
    return render_template('ngo/review_queue.html', 
                         user=user, 
                         pending_vaccinations=pending_vaccinations)

@ngo_bp.route('/review/<int:vaccination_id>', methods=['POST'])
@jwt_required()
def review_vaccination(vaccination_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != UserRole.NGO_ADMIN:
        return jsonify({'error': 'Access denied'}), 403
    
    vaccination = Vaccination.query.join(Animal).filter(
        Vaccination.id == vaccination_id,
        Animal.ngo_id == user.ngo_id
    ).first()
    
    if not vaccination:
        return jsonify({'error': 'Vaccination not found'}), 404
    
    action = request.json.get('action')
    comments = request.json.get('comments', '')
    
    if action == 'approve':
        vaccination.status = VaccinationStatus.APPROVED
        vaccination.reviewed_by = user.id
        vaccination.reviewed_at = datetime.utcnow()
        vaccination.review_comments = comments
        
        # Generate certificate (placeholder)
        # In production, generate actual PDF certificate
        vaccination.cert_url = f"/certificates/{vaccination.animal.udi}_{vaccination.id}.pdf"
        
        db.session.commit()
        
        flash('Vaccination approved and certificate generated', 'success')
        return jsonify({'status': 'approved'})
        
    elif action == 'reject':
        vaccination.status = VaccinationStatus.REJECTED
        vaccination.reviewed_by = user.id
        vaccination.reviewed_at = datetime.utcnow()
        vaccination.review_comments = comments
        
        db.session.commit()
        
        flash('Vaccination rejected', 'success')
        return jsonify({'status': 'rejected'})
    
    return jsonify({'error': 'Invalid action'}), 400

@ngo_bp.route('/animals')
@jwt_required()
def animals_list():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Animal.query.filter_by(ngo_id=user.ngo_id)
    
    if search:
        query = query.filter(
            db.or_(
                Animal.name.contains(search),
                Animal.udi.contains(search),
                Animal.breed.contains(search)
            )
        )
    
    animals = query.order_by(Animal.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('ngo/animals_list.html', 
                         user=user, 
                         animals=animals, 
                         search=search)

@ngo_bp.route('/donations')
@jwt_required()
def donations_list():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != UserRole.NGO_ADMIN:
        flash('Access denied - Admin only', 'error')
        return redirect(url_for('ngo.dashboard'))
    
    # Get donations for this NGO
    donations = Donation.query.filter_by(
        beneficiary_type=BeneficiaryType.NGO,
        beneficiary_ref=str(user.ngo_id)
    ).order_by(Donation.date.desc()).all()
    
    return render_template('ngo/donations.html', 
                         user=user, 
                         donations=donations)
