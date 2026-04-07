# Overview

FurrButler is a comprehensive ERP and marketplace platform for pet services. It targets various user types including pet parents, vendors, veterinarians, and government entities. The platform offers inventory management, booking systems, financial accounting, and a unique "FurrWings" pet passport system for international travel. It integrates with WhatsApp Business for vendor operations and features an AI-powered chatbot for business analytics. The project aims to provide a unified solution for the pet care industry, enhancing efficiency and connectivity across its diverse stakeholders.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend
The web application is built with React 18, Vite, and TypeScript, utilizing Tailwind CSS with shadcn/ui for a consistent and responsive user interface. It is designed as a Progressive Web App (PWA) with offline capabilities and implements role-based routing. GDPR compliance, including consent management, is integrated.

## Backend
The backend is a Flask application using an application factory pattern with modular blueprints. It employs SQLAlchemy as the ORM with Flask-Migrate for database management. Authentication is handled via JWT tokens with a robust role-based access control (RBAC) system supporting multiple user roles. Key features include comprehensive error handling, rate limiting, and CORS support.

## Database
The system uses SQLite for development and PostgreSQL for production. The database schema includes domains for users, pets, vendors, bookings, passport requests, and financial ledgers. It supports product inventory with FIFO batch tracking and detailed medical records with audit trails.

## Authentication & Authorization
A sophisticated RBAC system manages user roles and permissions. JWT-based authentication secures token management and includes session management, user preference tracking, and multi-language support.

## Business Logic
The platform includes specialized modules for inventory management, offering 14 standard inventory formulas (e.g., EOQ, ABC Analysis, Dead Stock Detection), comprehensive financial accounting with automated ledger entries, CRM functionality, and the FurrWings pet passport system. It also features a dynamic currency system allowing vendors to set their preferred currency, with INR as the default. Location-based filtering is implemented for services like groomers and marketplace vendors using Haversine distance calculations.

## AI & Analytics
An AI-powered chatbot uses machine learning for intent classification and business analytics, including TF-IDF vectorization and Logistic Regression. It supports regex-based NLP pattern matching, semantic similarity for fallback responses, and conversation logging for feedback-driven retraining. The analytics engine provides real-time insights based on the 14 inventory management formulas.

## Accounting Module
Enhanced accounting features include manual journal entry, dynamic invoice creation with GST calculation, GST summaries, and expense management with receipt uploads and budget tracking. It provides comprehensive financial reports like Balance Sheet, Cash Flow, and a professional CA Package with export options. New functionalities include Accounts Payable and Accounts Receivable with payment tracking, a Board Report for executive summaries, Budget Planning, and a customizable KPI Dashboard.

## HRM & Groomer System
This module supports comprehensive employee management, including review systems, certification tracking for groomers, and a "Groomer of the Month" award calculation. It includes features for leave management, timesheets, payroll generation, and performance reviews. Public routes allow customers to view groomer listings and profiles, and submit reviews. Security measures ensure data ownership and scope.

## CRM Module
The CRM module provides comprehensive customer relationship management for vendors. Key features include:
- **Customer Management** (`/erp/crm/customers`): View, filter, and manage customers with lifecycle stages and status tracking. Column indices account for the `marketing_opt_out` field (pet_count=29, interaction_count=30, last_interaction=31 in JOINed queries).
- **Customer Detail** (`/erp/crm/customer/<id>`): Full customer profile with inline interaction logging form, pet info, purchase history, and opportunities.
- **Interactions** (`/erp/crm/interactions`): Log and track all customer interactions (calls, emails, in-person, chat, etc.).
- **Tasks** (`/erp/crm/tasks`): Create, track, and complete follow-up tasks with priority levels and due dates.
- **Opportunity Pipeline** (`/erp/crm/opportunities`): Visual pipeline with 6 stages (prospecting → closed won/lost), stage movement buttons, and summary stats.
- **Promotions** (`/erp/crm/promotions`): Send promotional messages via in-app chat to eligible customers (respects `marketing_opt_out` flag). GDPR privacy notice included.
- **In-App Messaging** (`/erp/messages`): Vendor-side messaging interface with conversation list, chat panel, and new conversation creation. Uses `chat_conversations` and `chat_messages` tables.
- **Offline Data** (`/erp/crm/offline-data`): Collect and manage offline customer data with invitation system.
- **Security**: All customer-linked POST routes (interaction/task/opportunity creation) validate that the customer belongs to the current vendor.
- **Tables**: `crm_customers` (with `marketing_opt_out` column), `crm_pets`, `crm_interactions`, `crm_opportunities`, `crm_tasks`, `crm_campaigns`, `crm_campaign_members`, `crm_offline_data`, `chat_conversations`, `chat_messages`.

## JSON API v1 Module
A complete REST API under `/api/v1/` providing JSON versions of all pet parent routes. Uses JWT (PyJWT) authentication with Bearer tokens (30-day expiry). Key features:
- **Auth**: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- **Pets**: CRUD at `/api/v1/pets` and `/api/v1/pets/<index>`, including PUT for updates and passport documents at `/api/v1/pets/<index>/passport`
- **Vendors**: `/api/v1/vendor/<id>`, `/api/v1/vendor/<id>/groomers`, `/api/v1/vendor/<id>/slots`
- **Groomers**: `/api/v1/groomers` (location search), `/api/v1/groomer/<id>` (profile + reviews)
- **Bookings**: `POST /api/v1/bookings` (create), `GET /api/v1/bookings` (list), `POST /api/v1/bookings/<id>/review`
- **Marketplace**: `/api/v1/marketplace` (location search), `/api/v1/marketplace/vendor/<id>` (products)
- **Orders**: `GET/POST /api/v1/orders`
- **Handlers**: `/api/v1/handlers`, `/api/v1/handlers/<id>`, `POST /api/v1/handlers/<id>/book`, `GET /api/v1/handler-bookings`
- **Chat**: `/api/v1/chat/conversations`, `/api/v1/chat/<id>`, `POST /api/v1/chat/send`, `POST /api/v1/chat/start`
- **Location**: `/api/v1/vets`, `/api/v1/boarding`, `POST /api/v1/set-location`
- **Public (no auth)**: `/api/v1/community`, `/api/v1/stray-tracker`, `/api/v1/stray/<uid>`, `/api/v1/languages`
- **Config**: `JWT_SECRET` env var (defaults to dev key); helper functions `generate_token()` and `token_required` decorator at end of main.py
- **Dependencies**: PyJWT

## React Native Mobile App (Expo)
A complete React Native + Expo app in `/mobile/` that mirrors all pet parent functionality from the Jinja2 web app. Connects to the JSON API v1 endpoints.

### Structure
- `mobile/App.js` — Root component with AuthProvider, LocationProvider, SocketManager, and AppNavigator
- `mobile/src/screens/` — 40 screen files covering all pet parent features
- `mobile/src/components/` — 9 reusable UI components (Card, Button, Input, StarRating, Badge, etc.)
- `mobile/src/navigation/AppNavigator.js` — Full navigation: GDPR consent → Auth stack → Main tabs (Home, Discover, Bookings, Shop, Profile) with nested stack navigators
- `mobile/src/services/api.js` — API service layer with Axios, JWT auto-attach, 401 handling
- `mobile/src/context/AuthContext.js` — Auth state management (login, register, logout, token validation)
- `mobile/src/context/LocationContext.js` — GPS location with expo-location
- `mobile/src/constants/theme.js` — Colors, fonts, shadows, spacing matching the web app's purple gradient theme
- `mobile/src/constants/api.js` — API_BASE and SOCKET_URL configuration

### Screens (40 total)
Auth: Welcome, Login, Register, GDPRConsent | Pets: PetsList, AddPet, EditPet, PetDetail, Passport | Grooming: Groomers, GroomerListing, GroomerProfile, VendorProfile, Booking, Review | Marketplace: Marketplace, VendorShop, Cart, Orders | Handlers: Handlers, HandlerDetail, HandlerBook, HandlerInvoice, MyHandlerBookings | Chat: Conversations, Message | Location: Vets, Boarding, Discover (top tabs) | Community: Community, StrayTracker, StrayDetail | Profile: Profile, Settings, Notifications | FurrWings: FurrWingsServices, FurrWingsManagement | Other: ReportIssues, Home (dashboard)

### Key Features
- GDPR consent screen on first launch with required/optional checkboxes
- JWT auth with AsyncStorage persistence
- Location-based search with GPS support
- Socket.IO integration for real-time notifications
- Bottom tab navigation (Home, Discover, Bookings, Shop, Profile)
- Material top tabs for Discover (Groomers/Vets/Boarding)
- Web support via react-native-web
- Privacy settings with marketing opt-out, data download, account deletion

### Dependencies
expo ~51.0.0, react-native 0.74.0, @react-navigation/*, axios, socket.io-client, expo-location, @react-native-async-storage/async-storage, expo-image-picker, @expo/vector-icons

## FurrVet Module
The FurrVet module provides a dedicated interface for veterinarians. It includes dashboards, appointment management, patient records with detailed medical histories and vaccinations, billing, inventory management for vet supplies, laboratory services, and reporting tools. All templates share a consistent design with a fixed sidebar and are responsive. The module manages its own SQLite database (`furrvet.db`) for veterinary-specific data.

# External Dependencies

- **Core Frameworks**: Flask (with SQLAlchemy, JWT, Mail, Limiter), React 18 (with Vite, TypeScript), Tailwind CSS, shadcn/ui.
- **Database**: SQLite (development), PostgreSQL (production), Flask-Migrate.
- **Machine Learning & NLP**: scikit-learn, sentence-transformers, spaCy.
- **Communication**: Twilio (WhatsApp Business API - simulated), Flask-Mail.
- **File Management**: Werkzeug.
- **Analytics & Monitoring**: Google Analytics, Mixpanel (consent-gated).
- **Mapping/Location**: Nominatim API (for geocoding).