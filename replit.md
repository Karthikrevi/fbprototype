# Overview
FurrButler is an all-encompassing ERP and marketplace platform for the pet services industry, designed to streamline operations and connect various stakeholders including pet parents, vendors, veterinarians, and government entities. It features inventory management, booking systems, financial accounting, and a unique "FurrWings" pet passport for international travel. The platform integrates with WhatsApp Business and utilizes an AI-powered chatbot for business analytics, aiming to create a unified, efficient ecosystem for pet care.

# User Preferences
Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend
The web application is built with React 18, Vite, and TypeScript, utilizing Tailwind CSS with shadcn/ui for a responsive and consistent user interface. It functions as a Progressive Web App (PWA) with offline capabilities and implements role-based routing. GDPR compliance is integrated, including consent management. A React Native mobile application, developed with Expo, mirrors all pet parent functionalities and connects to the platform's JSON API.

## Backend
The backend is a Flask application using an application factory pattern with modular blueprints and SQLAlchemy as the ORM. Authentication is managed via JWT tokens with a robust role-based access control (RBAC) system. Key features include comprehensive error handling, rate limiting, and CORS support. A complete REST API under `/api/v1/` provides JSON versions of all pet parent routes.

## Database
The system uses SQLite for development and PostgreSQL for production, managed with Flask-Migrate. The schema supports users, pets, vendors, bookings, passport requests, and financial ledgers, including product inventory with FIFO batch tracking and detailed medical records with audit trails.

## Business Logic
The platform incorporates specialized modules for inventory management with 14 standard formulas, comprehensive financial accounting with automated ledger entries (including Accounts Payable/Receivable, budget planning, and KPI dashboards), CRM functionality, and the "FurrWings" pet passport system. It features a dynamic currency system and location-based filtering for services using Haversine distance. FurrVet is a Flask Blueprint (`furrvet_bp`, url_prefix='/furrvet') in `furrvet.py` handling veterinary clinic management with its own database (`furrvet.db`), session keys (`furrvet_vet_id`, `furrvet_vet_name`, `furrvet_vet_email`, `furrvet_clinic_name`), and werkzeug password hashing. The HRM module supports employee management, including reviews, certification tracking, and payroll.

## AI & Analytics
An AI-powered chatbot leverages machine learning for intent classification and business analytics, employing TF-IDF vectorization and Logistic Regression. It supports regex-based NLP pattern matching, semantic similarity for fallback responses, and conversation logging for retraining. The analytics engine provides real-time insights based on inventory management formulas.

## GDPR Compliance
The platform ensures full GDPR compliance across all portals, including privacy policies, terms of service, cookie consent, explicit consent for data processing (including medical data and international transfers), data export functionalities, and account deletion options. An admin breach log is also implemented.

## Route Audit & Hygiene
- **Logout routes**: Every portal has a dedicated logout (`/logout`, `/erp/logout`, `/vet/logout`, `/handler/logout`, `/ngo/logout`, `/furrvet/logout`, `/isolation/logout`, `/master/admin/logout` + `/admin/logout`), each scoped to only clear its own session keys
- **Admin auth**: Breach log checks `session.get("master_admin")`. `/admin/login` and `/admin/logout` are aliases for the master admin routes
- **Vendor login consolidated**: `/vendor-login` redirects to `/erp/login`. All vendor route auth redirects use `erp_login`
- **Cross-portal redirects**: `/login` and `/erp/login` redirect already-authenticated users to their correct dashboard (all 8 portals)
- **Employee management**: `/erp/hr/employees` renders `manage_employees.html` with employee list. `/erp/hr/employees/add` renders `employee_add.html` form with full fields (first/last name, email, phone, position, salary, hourly rate, join date, emergency contact, skills, certifications)
- **Portal dashboard helper**: `get_portal_dashboard()` Jinja global returns current portal's dashboard URL
- **All templates verified**: Every `render_template()` call in main.py has a corresponding template file

## Pet Data & Breeds System
- **Consolidated breeds data**: `/static/data/breeds.json` — 8 species (Dog with 215 breeds, Cat, Bird, Rabbit, Fish, Hamster, Reptile, Other) loaded dynamically via fetch
- **Blood types data**: `/static/data/blood_types.json` — capitalized species keys matching breeds.json, includes Dog, Cat, Rabbit, Bird, Fish, Hamster, Reptile, Other
- **Dynamic dropdowns**: `add_pet.html` and `edit_pet.html` use JavaScript to fetch breeds/blood types from static JSON, updating breed and blood type selects when species changes. Species values are now capitalized (Dog, Cat, etc.)
- **Pet reminders**: `pet_reminders` table in erp.db with fields: pet_index, user_email, reminder_type, title, description, due_date, priority (low/medium/high/urgent), source (manual/furrvet/system), vet_name, medication_name, dosage, frequency, is_completed
- **Reminder routes**: `/pet/<id>/reminder/add` (GET/POST), `/pet/<id>/reminder/<rid>/complete` (POST)
- **FurrVet bridge**: `bridge_furrvet_to_reminder()` utility function to push FurrVet prescriptions as pet parent reminders (matches by owner email and pet name)
- **Pet detail**: Shows real upcoming bookings from erp.db and active reminders; hardcoded 2024 data removed

## Pawsport System
- **Template**: `templates/pawsport.html` — multi-tab passport-style design with navy/gold theme
- **Database tables**: `pet_travel_history` (domestic/international travel records), `pawsport_documents` (uploaded documents with verification)
- **Routes**: `/pet/<id>/passport` (main pawsport view), `/pet/<id>/passport/add-travel` (POST log trip), `/pet/<id>/passport/upload-document` (POST upload doc)
- **5 tabs**: Identity (pet details + required documents checklist), Medical (vaccinations, medications, history + manual record form), Travel Bookings (upcoming bookings + handler bookings + document requirements), Domestic Journeys (stats + timeline), International Journeys (stats + timeline with stamps)
- **Required documents**: Microchip Certificate, Vaccination Records, Health Certificate, DGFT Certificate, AQCS Certificate, Quarantine Clearance — tracked for completion percentage
- **Uploads stored in**: `static/uploads/pawsport/`
- **Print support**: CSS print stylesheet formats Identity tab as A4 page
- **Tab persistence**: Selected tab saved in localStorage per pet

## Pet Insurance System
- **Database table**: `pet_insurance` in erp.db — tracks policies (provider, policy number, coverage type/amount, premiums, dates, claims contact, document URL, status)
- **Provider data**: `static/data/insurance_providers.json` — 4 providers (Digit, Bajaj Allianz, HDFC ERGO, Tata AIG) with multiple plans, species filtering, affiliate URLs
- **Routes**: `/pet/<id>/insurance` (browse + active policies), `/pet/<id>/insurance/add` (GET/POST track policy), `/pet/<id>/insurance/<pol_id>/cancel` (POST cancel)
- **Templates**: `pet_insurance.html` (plan comparison + active policies + disclaimer), `add_insurance.html` (form with provider dropdown, pre-selection support)
- **Auto reminders**: Adding a policy with end_date creates a high-priority renewal reminder 30 days before expiry
- **Document uploads**: Policy documents stored in `static/uploads/insurance/`
- **Entry points**: Quick action in pet_detail.html, insurance section in pawsport.html Medical tab
- **Column indices**: 0=id, 1=pet_index, 2=user_email, 3=provider_name, 4=policy_number, 5=coverage_type, 6=coverage_amount, 7=premium_monthly, 8=premium_annual, 9=start_date, 10=end_date, 11=claims_contact, 12=policy_document_url, 13=status, 14=created_at

## Pet Friendly Venues & Travel Affiliates
- **Affiliate data**: `static/data/travel_affiliates.json` — 4 hotel platforms (Booking.com, MakeMyTrip, Airbnb, Goibibo), 2 restaurant platforms (Zomato, Google Maps), 1 activity platform (Airbnb Experiences) with affiliate URLs, features, emojis
- **Database tables**: `pet_friendly_venues` (community-submitted venues), `venue_bookings` (legacy, routes redirect), `venue_reviews` (legacy, routes redirect)
- **No seed data**: Hardcoded 15 admin venues removed; only community-submitted approved venues shown
- **Routes**: `/pet-friendly` (affiliate cards + community venues), `/pet-friendly/suggest` (GET form + POST submit), `/pet-friendly/<id>` (redirect to /pet-friendly), `/pet-friendly/<id>/review` (redirect), `/pet-friendly/<id>/log-booking` (redirect), `/my-venue-bookings` (redirect)
- **Templates**: `pet_friendly.html` (affiliate cards, community section, disclaimer modal, travel tips), `suggest_venue.html` (form with Indian states dropdown, amenities checkboxes)
- **Disclaimer modal**: JavaScript modal warns users they are leaving FurrButler, mentions affiliate commission, advises verifying pet policies
- **Community venue suggestions**: `check_venue_submission()` for spam/duplicate detection with SSRF protection, auto-approve clean submissions, pending queue for flagged ones
- **Admin moderation**: `/admin/venues` dashboard with tabs (Pending/Flagged/Approved/Rejected), `/admin/venues/<id>/approve|reject|flag` actions
- **Admin template**: `admin_venues.html` (moderation dashboard)
- **Venue column indices**: 0=id, 1=name, 2=venue_type, 3=address, 4=city, 5=state, 6=pincode, 7=phone, 8=website, 9=google_maps_url, 10=booking_url, 11=latitude, 12=longitude, 13=pet_policy, 14=max_pet_size, 15=pet_fee, 16=amenities, 17=rating, 18=review_count, 19=verified, 20=is_active, 21=added_by, 22=created_at, 23=submission_status, 24=submitted_by_email, 25=submission_notes, 26=admin_notes, 27=google_verified, 28=flag_reason

## FurrWings Vet Connect Portal (Rebuilt)
- **Purpose**: Vet-facing portal for uploading pet health records, issuing travel certificates, connecting with pet parents
- **Design**: Clean white/navy blue (#0d47a1) with sidebar layout, no purple gradients
- **Auth**: Independent session (`furrwings_vet_id`, `furrwings_vet_name`, `furrwings_vet_email`, `furrwings_clinic`), registration requires admin approval
- **DB tables** (in erp.db): `furrwings_vets` (with erp_interests, years_experience, state, pincode, rejection_reason columns), `health_certificates`, `travel_vaccinations`, `furrwings_vet_activity`, `erp_integration_requests`
- **Routes** (in main.py): `/furrwings/vet/login`, `/furrwings/vet/register`, `/furrwings/vet/pending`, `/furrwings/vet/logout`, `/furrwings/vet/dashboard`, `/furrwings/vet/patients` (search), `/furrwings/vet/upload` (6 doc types), `/furrwings/vet/appointments`, `/furrwings/vet/certificates`, `/furrwings/vet/certificate/<id>`, `/furrwings/vet/certificate/<id>/print`, `/furrwings/vet/certificate/<id>/revoke`, `/furrwings/vet/settings`, `/furrwings/vet/erp-request` (POST), `/verify/cert/<hash>`
- **Admin routes**: `/admin/furrwings/vets`, `/admin/furrwings/vets/<id>/approve`, `/admin/furrwings/vets/<id>/reject` (with rejection reason)
- **Templates** (12 files, all in `templates/`): `furrwings_vet_login.html`, `furrwings_vet_register.html`, `furrwings_vet_pending.html`, `furrwings_vet_dashboard.html`, `furrwings_vet_patients.html`, `furrwings_vet_upload.html`, `furrwings_vet_appointments.html`, `furrwings_vet_cert_list.html`, `furrwings_vet_cert_view.html`, `furrwings_vet_cert_print.html`, `furrwings_vet_settings.html`, `verify_certificate.html`, `admin_furrwings_vets.html`
- **Upload types**: vaccine, prescription, lab_results, microchip, health_cert, general — saves to pet_reminders or health_certificates
- **health_certificates column indices**: [0]=id, [1]=certificate_number, [2]=vet_id, [3]=pet_name, [4]=pet_species, [5]=pet_breed, [6]=pet_dob, [7]=pet_microchip, [8]=owner_name, [9]=owner_email, [10]=owner_phone, [11]=destination_country, [12]=purpose, [13]=issue_date, [14]=expiry_date, [15]=examination_date, [16]=examination_findings, [17]=vaccinations_verified, [18]=parasites_treated, [19]=parasite_treatment_date, [20]=parasite_product, [21]=fit_for_travel, [22]=special_conditions, [23]=vet_signature, [24]=certificate_status, [25]=linked_pawsport_pet_index, [26]=linked_user_email, [27]=verification_hash, [28]=created_at
- **furrwings_vets column indices**: [0]=id, [1]=name, [2]=email, [3]=password, [4]=license_number, [5]=license_issuing_body, [6]=specialization, [7]=phone, [8]=clinic_name, [9]=clinic_address, [10]=city, [11]=state, [12]=pincode, [13]=furrvet_account_email, [14]=approval_status, [15]=approved_date, [16]=approved_by, [17]=certificate_count, [18]=is_active, [19]=created_at, [20]=erp_interests, [21]=years_experience, [22]=rejection_reason
- **Credentials**: vet@furrwings.com / vet123
- **Static uploads**: `static/uploads/furrwings/`

## FurrVet ERP (Clinical Routes)
- **Blueprint**: `furrvet_bp` in `furrvet.py`, prefix `/furrvet`
- **All templates** in `templates/furrvet/` (render_template paths include `furrvet/` prefix)
- **Clinical routes**: Patient CRUD, medical records (SOAP notes), vaccination management with certificates, lab tests with reference values, hospitalization with daily notes, invoicing with payment tracking, inventory/pharmacy management, staff management with certifications, appointment calendar, prescriptions
- **CRM/HRM/Accounting routes**: Client management with reminders, marketing campaigns, financial dashboard with P&L/AR/AP/GST reports, staff dashboard with reviews/certifications
- **Auth scoping**: All object-detail routes (view_invoice, view_medical_record, vaccination_certificate, view_prescription, pay_invoice, update_appointment, lab_results, hospitalization, discharge) scoped by `vet_id` in WHERE clauses to prevent IDOR
- **Session keys**: `furrvet_vet_id`, `furrvet_vet_name`, `furrvet_vet_email`, `furrvet_clinic_name`
- **Credentials**: vet@furrvet.com / vet123

# External Dependencies
- **Core Frameworks**: Flask, React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, React Native, Expo.
- **Database**: SQLite, PostgreSQL.
- **Machine Learning & NLP**: scikit-learn, sentence-transformers, spaCy.
- **Communication**: Twilio (simulated WhatsApp Business API), Flask-Mail.
- **Mapping/Location**: Nominatim API.