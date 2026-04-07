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

# External Dependencies
- **Core Frameworks**: Flask, React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, React Native, Expo.
- **Database**: SQLite, PostgreSQL.
- **Machine Learning & NLP**: scikit-learn, sentence-transformers, spaCy.
- **Communication**: Twilio (simulated WhatsApp Business API), Flask-Mail.
- **Mapping/Location**: Nominatim API.