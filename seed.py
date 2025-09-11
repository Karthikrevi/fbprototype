
#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from fbregistry.models import *
from fbregistry.services import generate_udi
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import random

app = create_app()

def seed_database():
    """Seed the database with initial data"""
    with app.app_context():
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        
        print("🔄 Creating initial data...")
        
        # Create NGOs
        ngos = []
        ngo_data = [
            {
                'name': 'Kerala Animal Welfare Society',
                'registration_number': 'KAWS2020001',
                'email': 'info@kaws.org',
                'phone': '+91-9876543210',
                'address': 'MG Road, Trivandrum',
                'district': 'Thiruvananthapuram'
            },
            {
                'name': 'Cochin SPCA',
                'registration_number': 'CSPCA2019001',
                'email': 'contact@cochinspca.org', 
                'phone': '+91-9876543211',
                'address': 'Marine Drive, Kochi',
                'district': 'Ernakulam'
            },
            {
                'name': 'Calicut Street Dog Care',
                'registration_number': 'CSDC2021001',
                'email': 'help@calicutdogs.org',
                'phone': '+91-9876543212',
                'address': 'SM Street, Kozhikode',
                'district': 'Kozhikode'
            }
        ]
        
        for ngo_info in ngo_data:
            ngo = NGO(**ngo_info)
            ngos.append(ngo)
            db.session.add(ngo)
        
        db.session.commit()
        print(f"✅ Created {len(ngos)} NGOs")
        
        # Create Users
        users = []
        user_data = [
            # NGO Users
            {
                'role': UserRole.NGO_ADMIN,
                'name': 'Priya Nair',
                'email': 'priya@kaws.org',
                'phone': '+91-9876543220',
                'ngo_id': ngos[0].id,
                'password_hash': generate_password_hash('admin123')
            },
            {
                'role': UserRole.NGO_FIELD,
                'name': 'Ravi Kumar',
                'email': 'ravi@kaws.org',
                'phone': '+91-9876543221',
                'ngo_id': ngos[0].id,
                'password_hash': generate_password_hash('field123')
            },
            {
                'role': UserRole.NGO_ADMIN,
                'name': 'Meera Joseph',
                'email': 'meera@cochinspca.org',
                'phone': '+91-9876543222',
                'ngo_id': ngos[1].id,
                'password_hash': generate_password_hash('admin123')
            },
            {
                'role': UserRole.NGO_ADMIN,
                'name': 'Suresh Pillai',
                'email': 'suresh@calicutdogs.org',
                'phone': '+91-9876543223',
                'ngo_id': ngos[2].id,
                'password_hash': generate_password_hash('admin123')
            },
            # Vet Users
            {
                'role': UserRole.VET,
                'name': 'Dr. Anjali Menon',
                'email': 'anjali.vet@gmail.com',
                'phone': '+91-9876543230',
                'ngo_id': None,
                'password_hash': generate_password_hash('vet123')
            },
            {
                'role': UserRole.VET,
                'name': 'Dr. Rajesh Kumar',
                'email': 'rajesh.vet@gmail.com',
                'phone': '+91-9876543231',
                'ngo_id': None,
                'password_hash': generate_password_hash('vet123')
            },
            # Gov User
            {
                'role': UserRole.GOV,
                'name': 'Sarah Thomas',
                'email': 'sarah.dhs@kerala.gov.in',
                'phone': '+91-9876543240',
                'ngo_id': None,
                'password_hash': generate_password_hash('gov123')
            }
        ]
        
        for user_info in user_data:
            user = User(**user_info)
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        print(f"✅ Created {len(users)} users")
        
        # Create Animals
        animals = []
        animal_names = ['Buddy', 'Luna', 'Max', 'Bella', 'Charlie', 'Lucy', 'Rocky', 'Molly', 'Tiger', 'Princess']
        breeds = ['Indian Pariah', 'Labrador', 'German Shepherd', 'Indie Mix', 'Golden Retriever', 'Beagle']
        colors = ['Brown', 'Black', 'White', 'Golden', 'Mixed', 'Spotted']
        
        # Coordinates for different districts
        locations = [
            {'lat': 8.5241, 'lng': 76.9366, 'ward_id': 'TVM001', 'district': 'TVM'},  # Trivandrum
            {'lat': 9.9312, 'lng': 76.2673, 'ward_id': 'EKM001', 'district': 'EKM'},  # Kochi
            {'lat': 11.2588, 'lng': 75.7804, 'ward_id': 'KZD001', 'district': 'KZD'},  # Kozhikode
        ]
        
        for i in range(20):
            location = random.choice(locations)
            ngo = random.choice(ngos)
            creator = random.choice([u for u in users if u.ngo_id == ngo.id])
            
            # Generate UDI
            udi, short_id = generate_udi(district_code=location['district'])
            
            animal = Animal(
                udi=udi,
                short_id=short_id,
                type=random.choice([AnimalType.STRAY, AnimalType.PET]),
                name=random.choice(animal_names) if random.random() > 0.3 else None,
                sex=random.choice(['Male', 'Female']),
                color=random.choice(colors),
                breed=random.choice(breeds),
                approx_age=random.choice(['Puppy', 'Young', 'Adult', 'Senior']),
                photos_json='[]',
                aggression_marker=random.choice(list(AggressionLevel)),
                ngo_id=ngo.id,
                lat=location['lat'] + random.uniform(-0.01, 0.01),
                lng=location['lng'] + random.uniform(-0.01, 0.01),
                accuracy_m=random.uniform(5, 50),
                ward_id=location['ward_id'],
                created_by=creator.id
            )
            animals.append(animal)
            db.session.add(animal)
        
        db.session.commit()
        print(f"✅ Created {len(animals)} animals")
        
        # Create Vaccinations
        vaccinations = []
        vaccine_types = ['Rabies', 'DHPP', 'Parvo', 'Distemper', 'Annual Booster']
        vaccine_brands = ['Nobivac', 'Vanguard', 'Duramune', 'Canigen']
        
        for animal in animals[:15]:  # Vaccinate 15 animals
            vax_count = random.randint(1, 3)
            for j in range(vax_count):
                verifier = random.choice([u for u in users if u.role in [UserRole.NGO_ADMIN, UserRole.NGO_FIELD, UserRole.VET]])
                
                vaccination = Vaccination(
                    animal_id=animal.id,
                    type=random.choice(vaccine_types),
                    brand=random.choice(vaccine_brands),
                    batch=f"B{random.randint(1000, 9999)}",
                    expiry=date.today() + timedelta(days=random.randint(365, 730)),
                    dose_ml=random.choice([1.0, 2.0, 0.5]),
                    route=random.choice(['SC', 'IM']),
                    site=random.choice(['Shoulder', 'Thigh', 'Neck']),
                    date_time=datetime.now() - timedelta(days=random.randint(1, 90)),
                    next_due=date.today() + timedelta(days=random.randint(30, 365)),
                    mode=random.choice([VaccinationMode.OUTDOOR, VaccinationMode.INDOOR]),
                    verifier_id=verifier.id,
                    status=random.choice([VaccinationStatus.APPROVED, VaccinationStatus.PENDING]),
                    lat=animal.lat,
                    lng=animal.lng,
                    accuracy_m=random.uniform(5, 20)
                )
                
                if vaccination.status == VaccinationStatus.APPROVED:
                    vaccination.reviewed_by = verifier.id
                    vaccination.reviewed_at = datetime.now()
                    vaccination.review_comments = "Approved after verification"
                
                vaccinations.append(vaccination)
                db.session.add(vaccination)
        
        db.session.commit()
        print(f"✅ Created {len(vaccinations)} vaccinations")
        
        # Create Donations
        donations = []
        donor_names = ['Anonymous Donor', 'Pet Lover Foundation', 'Local Community', 'Animal Rights Group']
        
        for i in range(25):
            donation = Donation(
                amount=random.uniform(500, 10000),
                donor_public=random.choice([True, False]),
                donor_name=random.choice(donor_names) if random.random() > 0.3 else f"Donor {i+1}",
                beneficiary_type=random.choice([BeneficiaryType.UDI, BeneficiaryType.NGO, BeneficiaryType.DRIVE]),
                beneficiary_ref=random.choice(animals).udi if random.random() > 0.5 else f"NGO-{random.choice(ngos).id}",
                date=datetime.now() - timedelta(days=random.randint(1, 180)),
                payment_ref=f"PAY{random.randint(100000, 999999)}",
                notes=f"Donation for animal welfare activities"
            )
            donations.append(donation)
            db.session.add(donation)
        
        db.session.commit()
        print(f"✅ Created {len(donations)} donations")
        
        # Create Donation Utilizations
        utilizations = []
        purposes = ['Vaccination supplies', 'Medical treatment', 'Food and shelter', 'Emergency care', 'Sterilization program']
        
        for donation in donations[:15]:  # Create utilizations for some donations
            utilization = DonationUtilization(
                donation_id=donation.id,
                status=random.choice([UtilizationStatus.COMPLETE, UtilizationStatus.PENDING]),
                amount_utilized=donation.amount * random.uniform(0.5, 1.0),
                purpose=random.choice(purposes),
                proof_urls_json='[]',
                notes=f"Utilized for {random.choice(purposes).lower()}",
                updated_by=random.choice([u for u in users if u.role == UserRole.NGO_ADMIN]).id
            )
            utilizations.append(utilization)
            db.session.add(utilization)
        
        db.session.commit()
        print(f"✅ Created {len(utilizations)} donation utilizations")
        
        print("\n🎉 Database seeded successfully!")
        print("\n📋 Login Credentials:")
        print("NGO Admin: priya@kaws.org / admin123")
        print("NGO Field: ravi@kaws.org / field123") 
        print("Veterinarian: anjali.vet@gmail.com / vet123")
        print("Government: sarah.dhs@kerala.gov.in / gov123")
        print("\n🔗 Access URLs:")
        print("NGO Portal: http://localhost:5000/ngo/login")
        print("Vet Portal: http://localhost:5000/vet/login")
        print("Gov Portal: http://localhost:5000/gov/login")
        print("Public Ledger: http://localhost:5000/v/public/ledger")

if __name__ == '__main__':
    seed_database()
