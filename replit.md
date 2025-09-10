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
The platform includes specialized modules for inventory management with advanced analytics (EOQ, turnover ratios, safety stock calculations), comprehensive financial accounting with automated ledger entries, CRM functionality for customer relationship management, and the FurrWings pet passport system for international travel documentation.

## AI & Analytics Components
An advanced chatbot system uses machine learning for intent classification and business analytics. It includes TF-IDF vectorization with logistic regression for query understanding, semantic similarity matching for fallback responses, and conversation logging with feedback-driven retraining capabilities. The analytics engine provides sophisticated business intelligence including inventory formulas, profit analysis, and operational insights.

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