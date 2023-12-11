# from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Tuple
from models.user import UserBase
from models.paper_pattern import CreatePaperPattern, CheckPaperPattern
from database.user import UserDB
from database.paper_pattern import PaperPatternDB
import datetime
from utils.helpers import helpers_single, helpers_multiple
from utils.user import (
    get_current_active_user,
    is_admin
)
import os
import openai
from google.cloud import vision

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] ='vision_key.json'
openai.api_key = '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'

router = APIRouter()
user_db = UserDB()
paper_pattern_db = PaperPatternDB()


@router.post('/create', summary="Create new paper pattern")
async def create_paper_pattern(data: CreatePaperPattern, current_user: UserBase = Depends(get_current_active_user)):
    paper_pattern_db.create_paper_pattern({
        "user_id": current_user["_id"],
        "subject": data.subject,
        "class_no": data.class_no,
        "title": data.title,
        "question_list": data.question_list,
    })
    return {"message": "Paper pattern created successfully"}

@router.get('/get-all/{subject}', summary="Get paper pattern")
async def get_paper_pattern(subject: str, current_user: UserBase = Depends(get_current_active_user)):
    paper_pattern = paper_pattern_db.get_all_paper_pattern(current_user["_id"], subject, None, 100)
    if not paper_pattern:
        raise HTTPException(status_code=404, detail="Paper pattern not found")
    return paper_pattern

@router.get('/get/{id}', summary="Get paper pattern by id")
async def get_paper_pattern_by_id(id: str, current_user: UserBase = Depends(get_current_active_user)):
    paper_pattern = paper_pattern_db.get_paper_pattern(current_user["_id"], id)
    if not paper_pattern:
        raise HTTPException(status_code=404, detail="Paper pattern not found")
    return paper_pattern

@router.post("/check", summary="Check paper pattern")
async def check_paper_pattern(data: CheckPaperPattern, current_user: UserBase = Depends(get_current_active_user)):
    vision_client = vision.ImageAnnotatorClient()
    image = vision.Image()
    total_marks = 0

    for list_data in data.list:
        image_url = list_data["answer_url"]

        try:
            # Download image content
            image_content = download_image_content(image_url)

            # Pass the downloaded content to Vision API
            image = vision.Image(content=image_content)
            response = vision_client.text_detection(image=image)

            list_data["student_answer"] = response.text_annotations[0].description

            prompt_text = generate_chat_prompt(
                f"main question number: {list_data['main_question']}\nsub question number: {list_data['sub_question']}\nanswer: {list_data['answer']}",
                list_data['student_answer'], 
                list_data['min_marks'], 
                list_data['max_marks']
            )

            # list_data["student_marks"] = await get_openai_response(prompt_text)
            list_data["student_marks"] = 5 # TODO: Remove this line after testing
            total_marks += int(list_data["student_marks"])

        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    
    # Save the result in the database
    paper_pattern_db.create_result({
        "user_id": current_user["_id"],
        "subject": data.subject,
        "paper_pattern_id": data.id,
        "student_branch": data.student_branch,
        "student_rollno": data.student_rollno,
        "list": data.list,
        "total_marks": total_marks,
        "created_at": datetime.datetime.now()
    })

    user_db.reduce_credits(current_user["_id"], 1)
        
    # print(data)
    return {"message": "Paper pattern checked successfully"}

@router.get('/get-all-results/{paper_pattern_id}', summary="Get paper pattern results")
async def get_paper_pattern_results(paper_pattern_id: str, current_user: UserBase = Depends(get_current_active_user)):
    results = paper_pattern_db.get_all_result(current_user["_id"], paper_pattern_id, None, 100)
    if not results:
        raise HTTPException(status_code=404, detail="Paper pattern results not found")
    return results


def generate_chat_prompt(teacher_ans, student_ans, min_marks, max_marks):
    # Define the conversation with the teacher and student answers
    conversation = f"""
    Teacher: {teacher_ans}
    Student: {student_ans}
    System: Provide marks between {min_marks} and {max_marks}.
    Teacher:
    """

    # Define the prompt for GPT-3
    prompt = f"Grade the following student's answer based on the provided teacher's answer. The minimum marks are {min_marks} and the maximum marks are {max_marks}.\n\n{conversation}"

    return prompt


async def get_openai_response(prompt):
    # Make the OpenAI API call
    response = openai.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
    )

    return response.choices[0].text.strip()


def download_image_content(image_url: str):
    import requests

    # Download image content
    response = requests.get(image_url)

    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to download image. Status code: {response.status_code}")

