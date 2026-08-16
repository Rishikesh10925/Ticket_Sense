from app.models.base import Base
from app.models.department import Department
from app.models.embedding import Embedding
from app.models.escalation import Escalation
from app.models.feedback import Feedback
from app.models.knowledge_base import KnowledgeBase
from app.models.ticket import Ticket
from app.models.user import User

__all__ = [
    "Base",
    "Department",
    "Embedding",
    "Escalation",
    "Feedback",
    "KnowledgeBase",
    "Ticket",
    "User",
]
