from pydantic import BaseModel


class CreateCheckoutSession(BaseModel):
    """
    Create a checkout session
    """
    num_students: int
    num_subjects: int
    num_semesters: int

class CheckTransaction(BaseModel):
    """
    Check a transaction
    """
    transaction_id: str


