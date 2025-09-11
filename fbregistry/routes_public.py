
from flask import Blueprint, render_template, jsonify, abort, request
from fbregistry.models import Animal, Vaccination, Donation, DonationUtilization
from fbregistry.services import verify_jws
from datetime import datetime

public_bp = Blueprint('public', __name__)

@public_bp.route('/<udi>')
def verify_udi(udi):
    """Public UDI verification page"""
    animal = Animal.query.filter_by(udi=udi).first()
    if not animal:
        abort(404)
    
    # Get latest vaccination
    latest_vaccination = Vaccination.query.filter_by(
        animal_id=animal.id,
        status='approved'
    ).order_by(Vaccination.date_time.desc()).first()
    
    # Get all approved vaccinations
    vaccinations = Vaccination.query.filter_by(
        animal_id=animal.id,
        status='approved'
    ).order_by(Vaccination.date_time.desc()).all()
    
    # Calculate vaccination status
    vaccination_status = 'Unknown'
    next_due = None
    
    if latest_vaccination:
        if latest_vaccination.next_due:
            if latest_vaccination.next_due > datetime.now().date():
                vaccination_status = 'Up to date'
            else:
                vaccination_status = 'Overdue'
            next_due = latest_vaccination.next_due
        else:
            vaccination_status = 'Vaccinated'
    else:
        vaccination_status = 'No vaccinations recorded'
    
    return render_template('public/verify.html',
                         animal=animal,
                         vaccinations=vaccinations,
                         latest_vaccination=latest_vaccination,
                         vaccination_status=vaccination_status,
                         next_due=next_due)

@public_bp.route('/ledger')
def public_ledger():
    """Public donation ledger"""
    # Get donations with public visibility
    donations = Donation.query.filter_by(donor_public=True).order_by(
        Donation.date.desc()
    ).limit(100).all()
    
    # Get utilization data
    utilizations = DonationUtilization.query.join(Donation).filter(
        Donation.donor_public == True
    ).order_by(DonationUtilization.updated_at.desc()).limit(50).all()
    
    # Calculate totals
    total_donations = sum(d.amount for d in donations)
    total_utilized = sum(u.amount_utilized for u in utilizations)
    utilization_rate = (total_utilized / total_donations * 100) if total_donations > 0 else 0
    
    return render_template('public/ledger.html',
                         donations=donations,
                         utilizations=utilizations,
                         total_donations=total_donations,
                         total_utilized=total_utilized,
                         utilization_rate=utilization_rate)

@public_bp.route('/api/verify/<udi>')
def api_verify_udi(udi):
    """API endpoint for UDI verification"""
    animal = Animal.query.filter_by(udi=udi).first()
    if not animal:
        return jsonify({'error': 'UDI not found'}), 404
    
    # Get latest vaccination
    latest_vaccination = Vaccination.query.filter_by(
        animal_id=animal.id,
        status='approved'
    ).order_by(Vaccination.date_time.desc()).first()
    
    result = {
        'udi': animal.udi,
        'type': animal.type.value,
        'name': animal.name,
        'breed': animal.breed,
        'sex': animal.sex,
        'aggression_level': animal.aggression_marker.value if animal.aggression_marker else None,
        'registered_date': animal.created_at.isoformat(),
        'vaccination_status': 'none'
    }
    
    if latest_vaccination:
        result['vaccination_status'] = 'vaccinated'
        result['last_vaccination'] = {
            'type': latest_vaccination.type,
            'date': latest_vaccination.date_time.isoformat(),
            'next_due': latest_vaccination.next_due.isoformat() if latest_vaccination.next_due else None
        }
        
        if latest_vaccination.next_due:
            if latest_vaccination.next_due > datetime.now().date():
                result['vaccination_status'] = 'up_to_date'
            else:
                result['vaccination_status'] = 'overdue'
    
    return jsonify(result)

@public_bp.route('/api/stats')
def api_public_stats():
    """Public statistics API"""
    from fbregistry.models import db
    
    stats = {
        'total_animals': Animal.query.count(),
        'total_strays': Animal.query.filter_by(type='s').count(),
        'total_pets': Animal.query.filter_by(type='p').count(),
        'total_vaccinations': Vaccination.query.filter_by(status='approved').count(),
        'total_donations': float(db.session.query(db.func.sum(Donation.amount)).scalar() or 0),
        'last_updated': datetime.now().isoformat()
    }
    
    return jsonify(stats)
