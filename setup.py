import os
import asyncio
import argparse
from database_manager import DatabaseManager
from services.auth_service import AuthService


async def setup_database():
    """Set up the database and create tables"""
    print("Setting up database...")
    db = DatabaseManager()
    await db.initialize_db()
    print("Database setup completed successfully.")
    return db


async def generate_admin_passwords(db):
    """Generate passwords for admin users"""
    print("Generating passwords for admin users...")
    auth_service = AuthService(db)
    await auth_service.generate_passwords_for_admins()
    print("Admin passwords have been generated and saved to users_passwords.json")


async def main():
    parser = argparse.ArgumentParser(description="Setup script for the Flask application")
    parser.add_argument('--init-db', action='store_true', help='Initialize the database')
    parser.add_argument('--gen-admin-passwords', action='store_true', help='Generate passwords for admin users')
    
    args = parser.parse_args()
    
    if args.init_db or args.gen_admin_passwords:
        db = await setup_database()
        
        if args.gen_admin_passwords:
            await generate_admin_passwords(db)
        
        await db.close()
    else:
        # If no arguments, run all setup steps
        db = await setup_database()
        await generate_admin_passwords(db)
        await db.close()
    
    print("Setup completed successfully.")


if __name__ == "__main__":
    asyncio.run(main()) 