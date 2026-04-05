# Overview

FurrButler is a comprehensive pet services ERP and marketplace platform built with a modern full-stack architecture. The system serves multiple user types including pet parents, vendors, veterinarians, handlers, isolation centers, NGOs, and government entities. At its core, it provides inventory management, booking systems, financial accounting, and a unique pet passport system called "FurrWings" for international travel documentation. The platform also includes a WhatsApp Business integration for vendor operations and an AI-powered chatbot for business analytics.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The web application is built with **React 18**, **Vite**, and **TypeScript** as the main frontend stack. It uses **Tailwind CSS** with **shadcn/ui** components for consistent styling and user interface elements. The application is designed as a **Progressive Web App (PWA)** with offline capabilities and includes role-based routing to serve different user types with appropriate interfaces. GDPR compliance is built-in with consent management and cookie banner functionality.

## Backend Architecture
The API backend follows a **Flask application factory pattern** with modular blueprint-based architecture. It uses **SQLAlchemy** as the ORM with **Flask-Migrate** for database management. Authentication is handled through **JWT tokens** with role-based access control (RBAC) supporting multiple user roles including admins, pet parents, vets, handlers, isolation centers, NGOs, and government users. The system includes comprehensive error handling, rate limiting, and CORS support.

## Database Design
The system uses **SQLite** for development and is designed to support **PostgreSQL** for production. The database schema includes separate domains for users, pets, vendors, bookings, passport requests, handler tasks, isolation stays, and NGO entities. Key tables include products with FIFO batch tracking, comprehensive financial ledgers, and detailed medical records with audit trails.

## Authentication & Authorization
A sophisticated RBAC system defines roles and permissions for different user types. JWT-based authentication provides secure token management with configurable expiration times. The system includes session management utilities and user preference tracking with multi-language support for Indian and international languages.

## Business Logic Modules
The platform includes specialized modules for inventory management with advanced analytics covering all 14 standard inventory formulas: EOQ, Reorder Point (ROP), Safety Stock, Inventory Turnover Ratio, Days Sales of Inventory (DSI), GMROI, ABC Analysis, Fill Rate, Inventory to Sales Ratio, Stock Cover Duration, Dead Stock Detection, Clearance Strategy, and comprehensive financial accounting with automated ledger entries, CRM functionality, and the FurrWings pet passport system.

## AI & Analytics Components
An advanced chatbot system uses machine learning for intent classification and business analytics. It includes TF-IDF vectorization with LogisticRegression (ngram_range 1-3, C=5.0) for query understanding, regex-based NLP pattern matching with priority-ordered intent resolution, semantic similarity matching for fallback responses, and conversation logging with feedback-driven retraining. The analytics engine (`chatbot/analytics_engine.py`) provides all 14 inventory management formulas with real-time database queries. NLP patterns (`chatbot/nlp_processor.py`) use priority ordering to resolve ambiguous queries (e.g., clearance vs restock). The classifier trains automatically on startup if no model exists.

# External Dependencies

## Core Framework Dependencies
- **Flask** with extensions for SQLAlchemy, JWT, Mail, and Limiter
- **React 18** with Vite build tooling and TypeScript support
- **Tailwind CSS** and shadcn/ui for frontend styling and components

## Database & Storage
- **SQLite** for development database with migration to **PostgreSQL** for production
- **Flask-Migrate** for database schema management and versioning

## Machine Learning & NLP
- **scikit-learn** for intent classification and analytics
- **sentence-transformers** for semantic similarity matching
- **spaCy** for natural language processing capabilities

## Communication Services
- **Twilio** integration for WhatsApp Business API (configured but in simulation mode)
- **Flask-Mail** for email notifications and communications

## File Management & Security
- **Werkzeug** for secure file uploads and handling
- Configurable upload folders with file type validation
- JWT-based authentication with configurable token expiration

## Analytics & Monitoring
- **Google Analytics** and **Mixpanel** integration (gated by user consent)
- Comprehensive logging and audit trail capabilities
- GDPR-compliant data retention and privacy management

## Development & Testing
- **Bootstrap 5** for responsive UI components
- Custom service worker for PWA functionality
- Comprehensive test suite infrastructure for chatbot and business logic

## Currency
- All HTML templates use ₹ (Indian Rupee) as default — not $ (USD)
- Font Awesome icons use `fa-rupee-sign` (not `fa-dollar-sign`)
- JS template literals in checkout/booking/POS use `₹${value}` format
- Exception: `business_analysis.html` retains USD for GPT API pricing references
- `ISO_4217_CURRENCIES` dict in main.py: ~160 currencies mapped to {symbol, name}
- `get_vendor_currency(vendor_id)`: returns vendor's currency symbol from settings_vendor; defaults to ₹
- `settings_vendor` table columns: id, vendor_id, gst_rate, platform_fee, razorpay_enabled, cod_enabled, auto_reports, currency, currency_symbol, standard_delivery_price, express_delivery_price, same_day_delivery_price, free_delivery_threshold
- Currency settings UI: Select2 searchable dropdown in accounting_settings.html with live preview
- Server-side validation: invalid/blank currency codes fall back to INR
- accounting_settings route uses `sqlite3.Row` for named column access (not numeric indices)

## Location-Based Filtering
- `haversine(lat1, lon1, lat2, lon2)`: calculates distance in km between two lat/lon points
- `geocode_location(query)`: uses Nominatim API to convert city/area/pincode to lat/lon
- `/set-location` route: stores GPS coordinates + reverse-geocoded city name in session
- `/groomers` route: filters vendors by `booking_radius_km` using haversine distance from search point
- `/marketplace` route: filters vendors by `delivery_radius_km` using haversine distance from search point
- Both routes support `?location=CityName` or `?city=CityName` URL params for text search
- Both routes fall back to `session["location"]` if no URL param provided
- Empty state shown when no location set; "no results" state when location set but no vendors in range
- `vendors` table has `booking_radius_km` (default 10.0) and `delivery_radius_km` (default 5.0) columns
- `edit_vendor_profile` route saves both radius fields; profile view displays them
- All coordinate checks use `is not None` guards (not truthiness) to handle 0.0 coordinates correctly

# FurrVet Module

## Templates (templates/furrvet/)
All FurrVet templates share a consistent design: 280px fixed sidebar with blue-to-teal gradient, Bootstrap 5.3.3 + Font Awesome 6, and responsive layout. The sidebar navigation includes links to Dashboard, Appointments, Patients, Medical Records, Laboratory, Billing, Inventory, Hospitalization, Reports, and Logout.

### Template-to-Route Mapping
- `furrvet_dashboard.html` — Dashboard with stats widgets and recent activity
- `furrvet_patients.html` — Patient list with species filter and search (pets JOIN pet_owners; owner_name=[17], owner_phone=[18])
- `furrvet_patient_detail.html` — Detailed pet profile with tabs for medical records, vaccinations, upcoming appointments (owner_name=[17], owner_email=[18], owner_phone=[19])
- `furrvet_appointments.html` — Appointment cards by date (appointments JOIN pets, pet_owners; pet_name=[13], species=[14], owner_name=[15], owner_phone=[16])
- `furrvet_new_appointment.html` — Form to schedule new appointment (pets tuple: id=[0], name=[1], owner_name=[2])
- `furrvet_billing.html` — Invoice table view (furrvet_invoices JOIN pets, pet_owners; pet_name=[18], owner_name=[19])
- `furrvet_inventory.html` — Inventory table with low-stock alerts (furrvet_inventory columns: item_name=[1], current_stock=[7], minimum_stock=[8])
- `furrvet_medical_records.html` — Medical record cards (medical_records JOIN pets, pet_owners; pet_name=[16], owner_name=[17])
- `furrvet_laboratory.html` — Lab tests and imaging records (currently mock data)
- `furrvet_reports.html` — Analytics with Chart.js doughnut/bar charts (stats dict: financial, appointments, total_patients, popular_services)
- `furrvet_hospitalization.html` — Hospitalization records (currently mock data)

## Database
- `furrvet.db` — SQLite database with tables: pets (17 cols), pet_owners (9 cols), appointments (13 cols), medical_records (16 cols), vaccinations (12 cols), furrvet_invoices (18 cols), furrvet_inventory (16 cols), vets
- All templates use numeric tuple indices for SQLite row access — must verify column positions when modifying queries