# Overview
FurrButler is an all-encompassing ERP and marketplace platform for the pet services industry. It aims to streamline operations and connect pet parents, vendors, veterinarians, and government entities within a unified, efficient ecosystem. Key capabilities include inventory management, booking systems, financial accounting, CRM, HRM, and a unique "FurrWings" pet passport for international travel. The platform also integrates with WhatsApp Business and utilizes AI for business analytics.

# User Preferences
Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend
The web application uses React 18, Vite, and TypeScript with Tailwind CSS and shadcn/ui for a responsive UI. It functions as a Progressive Web App (PWA) with offline capabilities and implements role-based routing and GDPR compliance. A React Native mobile application, built with Expo, mirrors pet parent functionalities.

## Backend
The backend is a Flask application utilizing an application factory pattern, modular blueprints, and SQLAlchemy. Authentication is managed via JWT tokens with a robust role-based access control (RBAC) system. It features comprehensive error handling, rate limiting, and CORS support, providing a complete REST API.

## Database
SQLite is used for development, and PostgreSQL for production, managed with Flask-Migrate. The schema supports users, pets, vendors, bookings, passport requests, and financial ledgers, including product inventory with FIFO batch tracking and detailed medical records with audit trails.

## Business Logic
The platform incorporates specialized modules for inventory management with 14 standard formulas, comprehensive financial accounting (including AP/AR, budgeting, KPI dashboards), CRM, HRM, and the "FurrWings" pet passport system. It features a dynamic currency system and location-based filtering using Haversine distance. A dedicated FurrVet blueprint handles veterinary clinic management.

## AI & Analytics
An AI-powered chatbot uses machine learning for intent classification and business analytics, employing TF-IDF vectorization and Logistic Regression. It supports regex-based NLP, semantic similarity for fallbacks, and conversation logging. The analytics engine provides real-time insights based on inventory management formulas.

## GDPR Compliance
Full GDPR compliance is ensured across all portals, covering privacy policies, consent management, data export, and account deletion options, including an admin breach log.

## Pet Management Systems
The platform includes consolidated pet breeds and blood types data, dynamic dropdowns for pet registration, pet reminder systems integrated with FurrVet prescriptions, and detailed pet profiles. The Pawsport system offers a multi-tab design for managing pet identity, medical records, and travel history (domestic and international) with document tracking and print support. A Pet Insurance system allows tracking policies, comparing providers, and generating renewal reminders.

## Pet-Friendly Venues & Affiliates
The platform features a system for pet-friendly venues, allowing community suggestions and admin moderation. It also integrates with travel affiliate platforms.

## FurrWings Vet Connect Portal
This vet-facing portal allows veterinarians to upload pet health records, issue travel certificates, and connect with pet parents. It includes vet registration with admin approval, patient management, document uploads, appointment tracking, and certificate generation with verification.

## FurrVet ERP (Clinical Routes)
A dedicated blueprint provides comprehensive clinical routes for patient CRUD, medical records (SOAP notes), vaccination management, lab tests, hospitalization, invoicing, pharmacy management, staff management, and appointment scheduling. All data access is scoped by `vet_id` to prevent IDOR vulnerabilities.

# External Dependencies
- **Core Frameworks**: Flask, React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, React Native, Expo.
- **Database**: SQLite, PostgreSQL.
- **Machine Learning & NLP**: scikit-learn, sentence-transformers, spaCy.
- **Communication**: Twilio (simulated WhatsApp Business API), Flask-Mail.
- **Mapping/Location**: Nominatim API.