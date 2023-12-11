from pydantic import BaseModel

class CreatePaperPattern(BaseModel):
    subject: str
    class_no: str
    title: str
    question_list: []

    class Config:
        arbitrary_types_allowed=True # This is required for the list of questions to be accepted


class CheckPaperPattern(BaseModel):
    subject: str
    id: str
    student_branch: str
    student_rollno: str
    list: []

    class Config:
        arbitrary_types_allowed=True # This is required for the list of answers to be accepted



