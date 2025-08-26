# backend/otp_service.py
from __future__ import annotations
import os
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from twilio.rest import Client
from sqlalchemy import select
from backend.db import db_session
from backend.models import OtpVerification, User
from backend.auth import verify_doctor_credentials

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# OTP Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3


class OTPService:
    """Service class for handling OTP verification"""

    def __init__(self):
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        else:
            self.client = None
            print("Warning: Twilio credentials not configured. OTP will be logged only.")

    # ----------------------------
    # Basic Utility Methods
    # ----------------------------
    def generate_otp(self) -> str:
        """Generate a 6-digit numeric OTP"""
        return ''.join(random.choices(string.digits, k=OTP_LENGTH))

    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS using Twilio or fallback to logging"""
        try:
            if not self.client or not TWILIO_PHONE_NUMBER:
                print(f"OTP for {phone_number}: {message}")
                return {
                    "success": True,
                    "sid": "test_message_id",
                    "status": "delivered"
                }

            message = self.client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            return {"success": True, "sid": message.sid, "status": message.status}

        except Exception as e:
            print(f"SMS sending failed: {e}")
            return {"success": False, "error": str(e)}

    # ----------------------------
    # OTP Lifecycle Methods
    # ----------------------------
    def create_otp_verification(
        self,
        phone_number: str,
        email: str,
        registration_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new OTP verification record and send OTP"""
        with db_session() as db:
            # Clean up pending OTPs
            existing = db.execute(
                select(OtpVerification).where(
                    OtpVerification.phone_number == phone_number,
                    OtpVerification.email == email,
                    OtpVerification.status == "pending"
                )
            ).scalars().all()
            for otp in existing:
                db.delete(otp)

            # Generate and store OTP
            otp_code = self.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

            otp_verification = OtpVerification(
                phone_number=phone_number,
                email=email,
                otp_code=otp_code,
                status="pending",
                expires_at=expires_at,
                registration_data=registration_data
            )
            db.add(otp_verification)
            db.flush()

            # Send OTP
            message = f"Your Medical RAG Chatbot verification code is: {otp_code}. Valid for {OTP_EXPIRY_MINUTES} minutes."
            sms_result = self.send_sms(phone_number, message)

            if sms_result["success"]:
                return {
                    "success": True,
                    "verification_id": otp_verification.id,
                    "expires_at": expires_at.isoformat(),
                    "message": f"OTP sent to {phone_number}"
                }
            else:
                db.delete(otp_verification)
                return {
                    "success": False,
                    "error": "Failed to send OTP",
                    "details": sms_result.get("error")
                }

    def verify_otp(
        self,
        phone_number: str,
        email: str,
        otp_code: str
    ) -> Dict[str, Any]:
        """Verify OTP code and update status"""
        with db_session() as db:
            otp_verification = db.execute(
                select(OtpVerification).where(
                    OtpVerification.phone_number == phone_number,
                    OtpVerification.email == email,
                    OtpVerification.status == "pending"
                ).order_by(OtpVerification.created_at.desc())
            ).scalar_one_or_none()

            if not otp_verification:
                return {"success": False, "error": "No pending OTP verification found"}

            if otp_verification.is_expired:
                otp_verification.status = "expired"
                return {"success": False, "error": "OTP has expired. Please request a new one."}

            if otp_verification.attempts_exhausted:
                otp_verification.status = "expired"
                return {"success": False, "error": "Maximum OTP attempts exceeded. Please request a new one."}

            # Increment attempts
            otp_verification.attempts += 1

            # Validate OTP
            if otp_verification.otp_code == otp_code:
                otp_verification.status = "verified"
                otp_verification.verified_at = datetime.utcnow()
                return {
                    "success": True,
                    "message": "OTP verified successfully",
                    "registration_data": otp_verification.registration_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Invalid OTP. {MAX_OTP_ATTEMPTS - otp_verification.attempts} attempts remaining."
                }

    def resend_otp(self, phone_number: str, email: str) -> Dict[str, Any]:
        """Resend a fresh OTP for an existing verification"""
        with db_session() as db:
            otp_verification = db.execute(
                select(OtpVerification).where(
                    OtpVerification.phone_number == phone_number,
                    OtpVerification.email == email,
                    OtpVerification.status == "pending"
                ).order_by(OtpVerification.created_at.desc())
            ).scalar_one_or_none()

            if not otp_verification:
                return {"success": False, "error": "No pending OTP verification found"}

            # Reset OTP
            otp_verification.otp_code = self.generate_otp()
            otp_verification.expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
            otp_verification.attempts = 0

            # Send OTP
            message = f"Your Medical RAG Chatbot verification code is: {otp_verification.otp_code}. Valid for {OTP_EXPIRY_MINUTES} minutes."
            sms_result = self.send_sms(phone_number, message)

            if sms_result["success"]:
                return {
                    "success": True,
                    "message": f"New OTP sent to {phone_number}",
                    "expires_at": otp_verification.expires_at.isoformat()
                }
            else:
                return {"success": False, "error": "Failed to resend OTP"}

    def cleanup_expired_otps(self):
        """Clean up expired OTPs from DB (periodic task)"""
        with db_session() as db:
            expired_otps = db.execute(
                select(OtpVerification).where(
                    OtpVerification.expires_at < datetime.utcnow(),
                    OtpVerification.status == "pending"
                )
            ).scalars().all()

            for otp in expired_otps:
                otp.status = "expired"

            print(f"Cleaned up {len(expired_otps)} expired OTP records")


# Global OTP service instance
otp_service = OTPService()
