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
The platform incorporates specialized modules for inventory management with 14 standard formulas, comprehensive financial accounting with automated ledger entries (including Accounts Payable/Receivable, budget planning, and KPI dashboards), CRM functionality, and the "FurrWings" pet passport system. It features a dynamic currency system and location-based filtering for services using Haversine distance. A dedicated FurrVet module handles veterinary-specific data, appointments, patient records, and billing. The HRM module supports employee management, including reviews, certification tracking, and payroll.

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

## Pet Friendly Venues System
- **Database tables**: `pet_friendly_venues` (venue details, pet policy, amenities, ratings), `venue_bookings` (user booking logs), `venue_reviews` (ratings + reviews)
- **Seed data**: 15 venues across Kerala, Goa, Bangalore, Mumbai, Delhi (hotels, resorts, cafes, parks)
- **Routes**: `/pet-friendly` (browse/filter), `/pet-friendly/<id>` (detail + reviews), `/pet-friendly/<id>/review` (POST), `/pet-friendly/<id>/log-booking` (GET/POST), `/my-venue-bookings` (user's bookings), `/pet-friendly/suggest` (POST suggestion)
- **Templates**: `pet_friendly.html` (grid with filters), `venue_detail.html` (detail + booking + reviews), `log_booking.html` (form), `my_venue_bookings.html` (booking list)
- **Entry points**: Dashboard tile in dashboard.html, quick action in pet_detail.html
- **Community venue suggestions**: `/pet-friendly/suggest` (GET form + POST submit), `check_venue_submission()` for spam/duplicate detection, auto-approve clean submissions, pending queue for flagged ones
- **Admin moderation**: `/admin/venues` dashboard with tabs (Pending/Flagged/Approved/Rejected), `/admin/venues/<id>/approve|reject|flag` actions
- **Templates**: `suggest_venue.html` (form with Indian states dropdown, amenities checkboxes), `admin_venues.html` (moderation dashboard)
- **Venue column indices**: 0=id, 1=name, 2=venue_type, 3=address, 4=city, 5=state, 6=pincode, 7=phone, 8=website, 9=google_maps_url, 10=booking_url, 11=latitude, 12=longitude, 13=pet_policy, 14=max_pet_size, 15=pet_fee, 16=amenities, 17=rating, 18=review_count, 19=verified, 20=is_active, 21=added_by, 22=created_at, 23=submission_status, 24=submitted_by_email, 25=submission_notes, 26=admin_notes, 27=google_verified, 28=flag_reason

# External Dependencies
- **Core Frameworks**: Flask, React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, React Native, Expo.
- **Database**: SQLite, PostgreSQL.
- **Machine Learning & NLP**: scikit-learn, sentence-transformers, spaCy.
- **Communication**: Twilio (simulated WhatsApp Business API), Flask-Mail.
- **Mapping/Location**: Nominatim API.