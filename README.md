# Bot Admin Dashboard

This project is a secure admin dashboard for managing a Telegram bot. It consists of a Flask API server and a Next.js TypeScript frontend.

## Project Structure

```
├── app.py                   # Main Flask server
├── database_manager.py      # Database connection manager
├── setup.py                 # Setup script for database initialization
├── requirements.txt         # Python dependencies
├── frontend/                # Next.js frontend
│   ├── src/                 # Frontend source code
│   ├── package.json         # Frontend dependencies
│   └── tsconfig.json        # TypeScript configuration
├── models/                  # Database models
└── services/                # Service classes
```

## Backend Features

- Secure authentication system with password hashing
- Session management with token-based authentication
- IP and user agent verification for session security
- Admin role-based access control
- Automatic password generation for admin users

## Frontend Features

- Modern Next.js application with TypeScript
- Secure authentication with token storage
- Session management
- Responsive design with Chakra UI

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Initialize the database and generate admin passwords:
   ```
   python setup.py --init-db --gen-admin-passwords
   ```

3. Start the Flask server:
   ```
   python app.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install Node.js dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

## API Endpoints

### Authentication

- `POST /api/auth/login` - Login with username and password
- `POST /api/auth/logout` - Logout and invalidate session
- `GET /api/auth/me` - Get current user information
- `GET /api/auth/sessions` - List active sessions (admin only)
- `DELETE /api/auth/sessions/:id` - Terminate a session (admin only)

### Users

- `GET /api/users/:id` - Get user details

### Spaces

- `GET /api/spaces` - List all spaces
- `GET /api/spaces/:id` - Get space details

## Security Features

- Secure password hashing with SHA-256
- Session tokens with expiration
- IP address and user agent verification
- HTTPS recommended for production
- CORS protection
- Role-based access control

## Environment Variables

### Backend

- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Secret key for session cookies
- `FLASK_DEBUG` - Enable debug mode
- `INIT_SECRET` - Secret for initialization operations

### Frontend

- `NEXT_PUBLIC_API_URL` - URL to the backend API 