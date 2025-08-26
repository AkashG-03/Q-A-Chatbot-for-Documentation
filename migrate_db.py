from __future__ import annotations
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_doctors():
    """Create sample doctors for testing"""
    from backend.db import db_session
    from backend.models import DoctorsRegistry
    
    sample_doctors = [
        {
            "legal_no": "MED001",
            "full_name": "Dr. Rajesh Kumar",
            "phone_number": "9876543210",
            "specialization": "Cardiology",
            "license_status": "active"
        },
        {
            "legal_no": "MED002", 
            "full_name": "Dr. Priya Sharma",
            "phone_number": "9876543211",
            "specialization": "Pediatrics",
            "license_status": "active"
        },
        {
            "legal_no": "MED003",
            "full_name": "Dr. Amit Patel",
            "phone_number": "9876543212", 
            "specialization": "Orthopedics",
            "license_status": "active"
        },
        {
            "legal_no": "MED004",
            "full_name": "Dr. Sarah Johnson",
            "phone_number": "9876543213", 
            "specialization": "Dermatology",
            "license_status": "active"
        },
        {
            "legal_no": "MED005",
            "full_name": "Dr. Michael Chen",
            "phone_number": "9876543214", 
            "specialization": "Neurology",
            "license_status": "active"
        },
        {
            "legal_no": "MED006",
            "full_name": "Dr. Emily Rodriguez",
            "phone_number": "9876543215", 
            "specialization": "Psychiatry",
            "license_status": "active"
        },
        {
            "legal_no": "MED007",
            "full_name": "Dr. James Wilson",
            "phone_number": "9876543216", 
            "specialization": "Emergency Medicine",
            "license_status": "active"
        }
    ]
    
    try:
        with db_session() as db:
            for doc_data in sample_doctors:
                # Check if doctor already exists
                existing = db.query(DoctorsRegistry).filter(
                    DoctorsRegistry.legal_no == doc_data["legal_no"]
                ).first()
                
                if not existing:
                    doctor = DoctorsRegistry(**doc_data)
                    db.add(doctor)
                    print(f"✅ Created doctor: {doc_data['full_name']} ({doc_data['legal_no']})")
                else:
                    print(f"⚠️ Doctor already exists: {doc_data['full_name']} ({doc_data['legal_no']})")
    
    except Exception as e:
        print(f"❌ Error creating sample doctors: {e}")

def main():
    """Main migration function"""
    try:
        print("🔧 Starting database migration...")
        print("=" * 50)
        
        # Import after path setup
        from backend.db import init_database
        from backend.models import Base
        
        print("📊 Initializing database tables...")
        init_database()
        print("✅ Database tables created successfully!")
        
        print("\n👨‍⚕️ Creating sample doctors for testing...")
        create_sample_doctors()
        print("✅ Sample doctors created successfully!")
        
        print("\n🎉 Database migration completed successfully!")
        print("=" * 50)
        print("\n📋 Test Credentials for Professional Registration:")
        print("License: MED001, Phone: 9876543210 - Dr. Rajesh Kumar (Cardiology)")
        print("License: MED002, Phone: 9876543211 - Dr. Priya Sharma (Pediatrics)")
        print("License: MED003, Phone: 9876543212 - Dr. Amit Patel (Orthopedics)")
        print("License: MED004, Phone: 9876543213 - Dr. Sarah Johnson (Dermatology)")
        print("License: MED005, Phone: 9876543214 - Dr. Michael Chen (Neurology)")
        print("License: MED006, Phone: 9876543215 - Dr. Emily Rodriguez (Psychiatry)")
        print("License: MED007, Phone: 9876543216 - Dr. James Wilson (Emergency Medicine)")
        print("\n🚀 You can now run: python run.py")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure all required dependencies are installed:")
        print("   pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("💡 Make sure PostgreSQL is running and connection details are correct in .env file")

if __name__ == "__main__":
    main()
