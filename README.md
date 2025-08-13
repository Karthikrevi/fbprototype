
# FurrButler - Pet Services ERP & Marketplace

A comprehensive pet services platform with ERP capabilities, international travel passport system (FurrWings), and GDPR-compliant data management.

## Architecture

### 🌐 Web App (`/web`)
- **React 18** + **Vite** + **TypeScript**
- **Tailwind CSS** + **shadcn/ui** components
- **PWA-ready** with offline capabilities
- **Role-based routing** for different user types
- **GDPR-compliant** consent management with cookie banner

### 🔧 API Backend (`/api`)
- **Flask** with app factory pattern
- **SQLAlchemy** + **Flask-Migrate** for database management
- **JWT authentication** with role-based access control
- **Blueprint-based** modular architecture
- **OpenAPI/Swagger** documentation

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (for production) / SQLite (for development)

### Development Setup

1. **Clone and setup environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

2. **Backend setup:**
```bash
cd api
pip install -r requirements.txt
flask db upgrade
flask seed-db
```

3. **Frontend setup:**
```bash
cd web
npm install
npm run dev
```

4. **Run both:**
```bash
# Terminal 1 (API)
cd api && flask run --host=0.0.0.0 --port=5000

# Terminal 2 (Web)
cd web && npm run dev
```

## User Roles & Features

### 👨‍👩‍👧‍👦 Pet Parents
- Pet profile management
- Service bookings (grooming, boarding, vet)
- FurrWings passport requests
- Order tracking

### 🏥 Veterinarians
- Patient management
- Medical records & prescriptions
- Vaccination certificates
- FurrWings health certifications

### ✈️ Handlers
- Travel coordination
- Document processing
- Status updates
- Escrow management

### 🏠 Isolation Centers
- Facility management
- Stay tracking
- Daily logs & media uploads

### 🐕 NGO Partners
- Stray dog registry
- Vaccination tracking
- Expense management
- Public transparency

### 🏛️ Government
- Read-only aggregate data
- Compliance reporting
- Data export capabilities

### ⚙️ Admin
- System management
- User administration
- Analytics & reporting

## Compliance & Security

- **GDPR compliance** with consent management
- **Data retention policies** defined in `/api/policies/`
- **F-DSC digital signatures** for document authenticity
- **Audit logging** for all sensitive operations
- **Role-based access control** (RBAC)

## API Documentation

OpenAPI specifications available at `/api/docs` when running in development mode.

## Contributing

See `docs/CONTRIBUTING.md` for development guidelines.

## License

MIT License - see LICENSE file for details.
