# Sinthanai's Exam Portal

KGiSL Institute of Technology - Exam Management System

## Features

- **Admin Dashboard**: Upload seating plans, manage datasets, toggle active exams
- **Student Portal**: View hall seating details, exam information
- **Excel Upload**: Supports both .xls and .xlsx formats, including corrupted database exports
- **Mobile Responsive**: Works seamlessly on all devices

## Tech Stack

### Backend
- Django 5.2.9
- Django REST Framework
- Python 3.x
- SQLite Database

### Frontend
- Next.js 16.0.10
- React
- Tailwind CSS
- Framer Motion
- Axios

## Installation

### Backend Setup
```bash
cd d:\adminstudent
pip install -r requirements.txt
python manage.py migrate
python create_admin.py  # Create admin user
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Usage

### Admin Login
1. Navigate to http://localhost:3000
2. Select "Admin" role
3. Login with admin credentials
4. Upload seating plan (.xls or .xlsx)
5. Toggle dataset to activate

### Student Login
1. Navigate to http://localhost:3000
2. Select "Student" role
3. Enter register number and password
4. View hall seating details

## Deployment

### Quick Deploy to Render

1. Push code to GitHub
2. Go to [Render](https://render.com) → **New** → **Blueprint**
3. Connect repository and click **Apply**
4. Configure environment variables:
   - **Backend**: `ALLOWED_HOSTS`, `FRONTEND_URL`
   - **Frontend**: `NEXT_PUBLIC_API_URL`
5. Redeploy both services

See [Quick Start Guide](docs/quick_start.md) or [Full Deployment Guide](docs/deployment_guide.md) for details.

### Environment Variables

- Backend uses PostgreSQL (auto-configured by Render)
- Frontend connects via `NEXT_PUBLIC_API_URL`
- All settings support environment-based configuration

## License

© 2025 KGiSL Institute of Technology
