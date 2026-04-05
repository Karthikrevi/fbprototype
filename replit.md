# Overview

FurrButler is a comprehensive pet services ERP and marketplace platform built with Flask (Python). The system serves multiple user types including pet parents, vendors, veterinarians, handlers, isolation centers, NGOs, and government entities. It provides inventory management, booking systems, financial accounting, and a pet passport system called "FurrWings" for international travel documentation. Includes WhatsApp Business integration and an AI-powered chatbot for business analytics.

# User Preferences

Preferred communication style: Simple, everyday language.
Currency: Indian Rupee (₹)

# System Architecture

## Frontend Architecture
Server-side rendered with Jinja2 templates, Bootstrap 5, and Font Awesome icons. The `/web` directory has a separate React/Vite frontend but the main app runs as a monolithic Flask server.

## Backend Architecture
Single Flask application in `main.py` (~11,000 lines) with SQLite databases (`erp.db`, `furrvet.db`). Uses Flask-SocketIO for real-time features. User/pet data stored via `replit_db_shim.py` (SQLite-based key-value store replacing the old Replit DB). Vendor ERP, marketplace, FurrWings, FurrVet, and NGO modules all defined as routes in `main.py`.

## Database Design
**SQLite** databases: `erp.db` (main ERP), `furrvet.db` (veterinary), `kv_store.db` (user/pet data shim). Tables include vendors, products, bookings, sales_log, reviews, handler_profiles, stray_dogs, ngo_partners, passport_documents, and many more.

## Authentication & Authorization
Session-based auth with separate login flows for pet parents, vendors, vets, handlers, isolation centers, NGOs, and master admin. No JWT — uses Flask sessions.

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