"""
Conversation Memory Manager
Handles storing and retrieving conversation context for personalized AI interactions
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from db.models import ConversationContext


class ConversationMemoryManager:
    """Manages conversation context and memory across sessions"""

    DEFAULT_EXPIRY_HOURS = 24

    @staticmethod
    def get_or_create_context(
        session_id: str,
        patient_email: str,  # NOW REQUIRED - not optional
        db: Session
    ) -> ConversationContext:
        """
        Get existing context or create new one

        CRITICAL SECURITY: Contexts are isolated by BOTH session_id AND patient_email
        to prevent conversation leakage between users
        """
        if not patient_email:
            raise ValueError("patient_email is required for user isolation. Cannot create context without user identifier.")

        # **USER ISOLATION: Query by BOTH session_id AND patient_email**
        context = db.query(ConversationContext).filter(
            ConversationContext.session_id == session_id,
            ConversationContext.patient_email == patient_email  # ← CRITICAL: User isolation
        ).first()

        if not context:
            expires_at = datetime.now() + timedelta(
                hours=ConversationMemoryManager.DEFAULT_EXPIRY_HOURS
            )

            context = ConversationContext(
                session_id=session_id,
                patient_email=patient_email,
                context_data={},
                expires_at=expires_at
            )
            db.add(context)
            db.commit()
            db.refresh(context)

        return context

    @staticmethod
    def update_context(
        session_id: str,
        patient_email: str,  # NOW REQUIRED for user isolation
        updates: Dict[str, Any],
        db: Session
    ) -> ConversationContext:
        """
        Update conversation context with new information

        CRITICAL SECURITY: Requires both session_id AND patient_email
        """
        if not patient_email:
            raise ValueError("patient_email is required for user isolation")

        # **USER ISOLATION: Query by BOTH session_id AND patient_email**
        context = db.query(ConversationContext).filter(
            ConversationContext.session_id == session_id,
            ConversationContext.patient_email == patient_email
        ).first()

        if not context:
            return None

        # Merge updates into context_data
        if context.context_data is None:
            context.context_data = {}

        for key, value in updates.items():
            context.context_data[key] = value

        context.updated_at = datetime.now()

        # Mark as modified for JSON column
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(context, "context_data")

        db.commit()
        db.refresh(context)

        return context

    @staticmethod
    def save_doctor_selection(
        session_id: str,
        patient_email: str,
        doctor_id: int,
        doctor_name: str,
        specialization: str,
        db: Session
    ):
        """Save selected doctor to context - USER ISOLATED"""
        if not patient_email:
            raise ValueError("patient_email required for user isolation")

        updates = {
            "selected_doctor": {
                "id": doctor_id,
                "name": doctor_name,
                "specialization": specialization,
                "selected_at": datetime.now().isoformat()
            }
        }
        return ConversationMemoryManager.update_context(session_id, patient_email, updates, db)

    @staticmethod
    def save_attempted_date(
        session_id: str,
        patient_email: str,
        date: str,
        rejection_reason: Optional[str],
        db: Session
    ):
        """Save attempted booking date and rejection reason - USER ISOLATED"""
        if not patient_email:
            raise ValueError("patient_email required for user isolation")

        # **USER ISOLATION: Query by BOTH**
        context = db.query(ConversationContext).filter(
            ConversationContext.session_id == session_id,
            ConversationContext.patient_email == patient_email
        ).first()

        if not context:
            return None

        if context.context_data is None:
            context.context_data = {}

        # Add to attempted dates list
        if "attempted_dates" not in context.context_data:
            context.context_data["attempted_dates"] = []

        if date not in context.context_data["attempted_dates"]:
            context.context_data["attempted_dates"].append(date)

        # Save rejection reason
        if rejection_reason:
            context.context_data["last_rejection_reason"] = rejection_reason
            context.context_data["rejection_history"] = context.context_data.get(
                "rejection_history", []
            )
            context.context_data["rejection_history"].append({
                "date": date,
                "reason": rejection_reason,
                "timestamp": datetime.now().isoformat()
            })

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(context, "context_data")

        db.commit()
        db.refresh(context)

        return context

    @staticmethod
    def save_successful_booking(
        session_id: str,
        patient_email: str,
        appointment_id: int,
        doctor_name: str,
        date: str,
        time: str,
        db: Session
    ):
        """Save successful booking to context - USER ISOLATED"""
        if not patient_email:
            raise ValueError("patient_email required for user isolation")

        updates = {
            "last_successful_booking": {
                "appointment_id": appointment_id,
                "doctor_name": doctor_name,
                "date": date,
                "time": time,
                "booked_at": datetime.now().isoformat()
            }
        }
        return ConversationMemoryManager.update_context(session_id, patient_email, updates, db)

    @staticmethod
    def update_message_count(
        session_id: str,
        patient_email: str,
        user_message: str,
        ai_response: str,
        db: Session
    ):
        """Update message count and last messages - USER ISOLATED"""
        if not patient_email:
            raise ValueError("patient_email required for user isolation")

        # **USER ISOLATION: Query by BOTH**
        context = db.query(ConversationContext).filter(
            ConversationContext.session_id == session_id,
            ConversationContext.patient_email == patient_email
        ).first()

        if not context:
            return None

        context.last_message = user_message
        context.last_response = ai_response
        context.message_count = (context.message_count or 0) + 1
        context.updated_at = datetime.now()

        db.commit()
        db.refresh(context)

        return context

    @staticmethod
    def get_context_for_prompt(
        session_id: str,
        patient_email: str,
        db: Session
    ) -> str:
        """
        Generate context string to inject into AI prompt
        This helps AI remember previous interactions

        CRITICAL SECURITY: Only retrieves context for the specified user
        """
        if not patient_email:
            # No user email = no context (security: prevent context leakage)
            return ""

        # **USER ISOLATION: Query by BOTH**
        context = db.query(ConversationContext).filter(
            ConversationContext.session_id == session_id,
            ConversationContext.patient_email == patient_email
        ).first()

        if not context or not context.context_data:
            return ""

        context_parts = []

        # Selected doctor
        if "selected_doctor" in context.context_data:
            doctor = context.context_data["selected_doctor"]
            context_parts.append(
                f"The user has previously shown interest in {doctor['name']} "
                f"({doctor['specialization']})."
            )

        # Attempted dates
        if "attempted_dates" in context.context_data and context.context_data["attempted_dates"]:
            dates = context.context_data["attempted_dates"]
            context_parts.append(
                f"The user has attempted to book on: {', '.join(dates)}."
            )

        # Last rejection
        if "last_rejection_reason" in context.context_data:
            reason = context.context_data["last_rejection_reason"]
            context_parts.append(
                f"Last booking attempt failed because: {reason}"
            )

        # Previous successful booking
        if "last_successful_booking" in context.context_data:
            booking = context.context_data["last_successful_booking"]
            context_parts.append(
                f"User successfully booked an appointment (ID: {booking['appointment_id']}) "
                f"with {booking['doctor_name']} on {booking['date']} at {booking['time']}."
            )

        # Conversation summary
        if "conversation_summary" in context.context_data:
            context_parts.append(
                f"Summary: {context.context_data['conversation_summary']}"
            )

        if context_parts:
            return "**Conversation Context:**\n" + "\n".join(f"- {part}" for part in context_parts)

        return ""

    @staticmethod
    def cleanup_expired_contexts(db: Session) -> int:
        """Remove expired conversation contexts"""
        expired = db.query(ConversationContext).filter(
            ConversationContext.expires_at < datetime.now()
        ).all()

        count = len(expired)
        for context in expired:
            db.delete(context)

        db.commit()
        return count

    @staticmethod
    def extend_expiry(session_id: str, patient_email: str, hours: int, db: Session):
        """Extend the expiry time of a conversation context - USER ISOLATED"""
        if not patient_email:
            raise ValueError("patient_email required for user isolation")

        # **USER ISOLATION: Query by BOTH**
        context = db.query(ConversationContext).filter(
            ConversationContext.session_id == session_id,
            ConversationContext.patient_email == patient_email
        ).first()

        if context:
            context.expires_at = datetime.now() + timedelta(hours=hours)
            db.commit()
            db.refresh(context)

        return context
