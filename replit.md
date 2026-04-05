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

## Accounting Module Improvements
- **Journal Entry** (`/erp/finance/journal-entry`): Manual ledger entry with debit/credit, account selection, reference numbers; `entry_source` column in `ledger_entries` tracks 'manual' vs 'auto'
- **Invoice Creation** (`/erp/finance/invoice/create`): Dynamic line items, GST calculation, generates printable invoice view; records in `orders` + `order_items` + `ledger_entries`
- **GST Summary** (`/erp/finance/gst-summary`): Date-range filter, output/input tax breakdown, CSV export; calculates GST from sales_log and expenses
- **Expense Management** (`/erp/reports/expenses`): Receipt file upload (stored in `static/uploads/receipts/`), monthly budget tracking per category via `expense_budgets` table, budget-vs-actual progress bars
- **Balance Sheet** (`/erp/finance/balance-sheet`): Fixed assets from `fixed_assets` table, liabilities from ledger AP entries, owner's equity from `capital_accounts` table (no more hardcoded values)
- **Cash Flow** (`/erp/finance/cash-flow`): Investing from `fixed_assets` purchases, financing from `capital_accounts`, beginning cash calculated from historical data
- **Quick Actions**: 6 gradient action buttons on accounting dashboard linking to Journal Entry, Add Expense, Create Invoice, GST Summary, Balance Sheet, Cash Flow
- **Accounts Payable** (`/erp/finance/accounts-payable`): CRUD for payable entries with `payable_entries` table; inline payment recording via `/erp/finance/payable/pay/<id>`; double-entry ledger (debit AP, credit Cash/Bank); payment history from `payment_records` table; categories: Supplier, Rent, Utilities, Salaries, Equipment, Services, Other
- **Accounts Receivable** (`/erp/finance/accounts-receivable`): CRUD for receivable entries with `receivable_entries` table; inline payment recording via `/erp/finance/receivable/pay/<id>`; double-entry ledger (debit Cash/Bank, credit AR); payment history; overdue detection
- **New DB tables**: `expense_budgets`, `fixed_assets`, `capital_accounts`, `payable_entries`, `receivable_entries`, `payment_records`
- **New columns**: `ledger_entries.entry_source`, `expenses.receipt_url`
- **Context processor**: `now_date` injected into all templates for date comparisons
- **CA Package** (`/erp/finance/ca-package`): Professional financial reports page with P&L, GST, Balance Sheet, Ledger, Expenses, Sales summaries; Chart.js expense bar chart; balance check indicator; ZIP download with all 6 CSVs; individual CSV export routes at `/erp/finance/ca-package/export/{pnl,gst,balance-sheet,ledger,expenses,sales}`
- **CSV Export Routes**: `/erp/reports/pnl/export` (P&L CSV), `/erp/reports/ledger/export` (General Ledger CSV with running balance)
- **Dummy Button Fixes**: All `href="#"` and placeholder `alert()` buttons in served vendor ERP templates replaced with working links — profit_loss.html, general_ledger.html, manage_time_slots.html, erp_vendor_dashboard.html, financial_planning.html
- **Board Report** (`/erp/finance/board-report`): 6-page printable professional business report with Cover, Executive Summary (auto-generated narrative), Financial Performance (Chart.js revenue line + expense doughnut + comparison table), Business Operations (top products/services tables), Financial Position (balance sheet), KPIs & Outlook; print/PDF buttons; disclaimer notice; navy/white design
- **Budget Planning** (`/erp/finance/budget` GET/POST): Revenue target + 8 expense category budgets; saves to `expense_budgets` table; progress bars with color coding; budget vs actual comparison; purple gradient ERP styling
- **KPI Dashboard** (`/erp/finance/kpi-dashboard`): 10 default KPIs with real data (revenue, growth, margin, customers, AOV, inventory turnover, bookings, rating, dead stock, staff productivity); health ring; status badges (On Target/At Risk/Off Track); trend arrows; personalisation section to add/remove custom KPIs from 10 additional options; `vendor_kpis` table for custom KPI storage

## Dynamic Vendor Currency
- `get_vendor_currency(vendor_id)` and `get_vendor_id_from_email(email)` registered as Jinja2 globals
- Flask context processor `inject_vendor_currency()` auto-injects `vendor_currency` (and `vendor_id`) into all templates when vendor is logged in
- 36 vendor ERP templates use `{{ vendor_currency }}` instead of hardcoded ₹
- Pet parent, NGO, FurrVet, FurrWings, admin, passport templates remain unchanged with hardcoded ₹
- `accounting_settings.html` Jinja2 default fallback ('₹') and JS currency list entries kept as-is
- Default currency is ₹ (INR) when no vendor setting exists

## HRM & Groomer System
- **DB tables**: `employee_reviews` (multi-criteria ratings), `certified_groomers` (certification records), `groomer_of_month` (monthly awards)
- **Employee columns added**: `avg_overall_rating`, `total_reviews`, `is_certified`, `is_groomer_of_month` on `employees` table; `employee_id` on `bookings` table
- **Routes (vendor-auth)**: `/erp/hr/employees/<id>` (detail), `/erp/hr/employees/<id>/edit` (edit), `/erp/hr/leaves` (leave management), `/erp/hr/timesheets` + `/save` + `/mark-attendance`, `/erp/hr/payroll` + `/pay/<id>` + `/generate-payslips`, `/erp/hr/performance/add`, `/erp/bookings/done/<id>`, `/erp/bookings/extend/<id>`, `/erp/bookings/assign-staff/<id>`, `/erp/certifications/check`, `/erp/hr/groomer-of-month/calculate`
- **Routes (public/customer)**: `/vendor/<id>/groomers` (groomer listing), `/groomer/<id>` (groomer profile), `/booking/<id>/review` (customer rating)
- **Templates**: `employee_detail.html`, `employee_edit.html`, `employee_leaves.html`, `manage_timesheets.html`, `manage_payroll.html`, `payslips.html`, `performance_review_form.html`, `booking_review.html`, `groomer_listing.html`, `groomer_profile.html`
- **Certification criteria**: 50+ reviews, avg rating >= 4.8, >= 85% would_book_again, >= 180 days tenure
- **GOTM calculation**: weighted score (review_count * 0.4 + avg_rating * 0.6 * 10) for current month
- **Security**: All employee-modifying POST routes verify employee belongs to current vendor (ownership check); Socket.IO events scoped to customer email rooms (not broadcast)
- **Auto-CRM**: `auto_crm_collection()` populates CRM on booking completion; `update_employee_review_stats()` syncs rating/certification status

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