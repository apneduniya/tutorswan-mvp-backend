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
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

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
        image_url_url = list_data["answer_url_list"]
        list_data["student_answer"] = ""

        for image_url in image_url_url:
            try:
                # Download image content
                image_content = download_image_content(image_url)

                # Pass the downloaded content to Vision API
                image = vision.Image(content=image_content)
                response = vision_client.text_detection(image=image)

                list_data["student_answer"] += response.text_annotations[0].description

            except Exception as e:
                print(e)
                raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
            
        # prompt_text = generate_chat_prompt(
        #     f"main question number: {list_data['main_question']}\nsub question number: {list_data['sub_question']}\nanswer: {list_data['answer']}",
        #     list_data['student_answer'], 
        #     list_data['min_marks'], 
        #     list_data['max_marks']
        # )

        student_answer_embedding = get_embedding(list_data["student_answer"], model='text-embedding-ada-002')
        teacher_answer_embedding = get_embedding(list_data["answer"], model='text-embedding-ada-002')

        # Convert the embeddings to numpy arrays
        student_answer_embedding = np.array(student_answer_embedding)
        teacher_answer_embedding = np.array(teacher_answer_embedding)

        # Calculate cosine similarity
        cosine_similarity_score = cosine_similarity([student_answer_embedding], [teacher_answer_embedding])[0][0]

        # Calculate marks
        list_data["student_marks"] = int(round(cosine_similarity_score * (list_data["max_marks"] - list_data["min_marks"]) + list_data["min_marks"]))

        # list_data["student_marks"] = await get_openai_response(prompt_text)
        # print("Teacher answer: ", list_data["answer"])
        # print("Student answer: ", list_data["student_answer"])
        # print("Marks alloted by GPT: ", list_data["student_marks"])
        # list_data["student_marks"] = 5 # TODO: Remove this line after testing
        # total_marks += int(list_data["student_marks"])

        # Take only number from the response
        # total_marks += int(''.join(filter(str.isdigit, list_data["student_marks"])))
        total_marks += int(list_data["student_marks"])
    
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
    Now you are a teacher and you have to grade the student's answer based on the provided teacher's answer.
    Teacher: {teacher_ans}
    Student: {student_ans}
    Teacher gives marks to the student's answer only in numbers within range of {min_marks} and {max_marks}. 
    The marks:
    """

    # Define the prompt for GPT-3
    prompt = f"""Behave like a teacher and grade the following student's answer based on the provided teacher's answer. The minimum marks are {min_marks} and the maximum marks are {max_marks}.\n\n{conversation}
    Example 1:
    Teacher: 2
    Student: 2
    Teacher gives marks to the student's answer only in numbers within range of 0 and 5.
    The marks: 2

    Example 2:
    Teacher: This is a cat with a hat.
    Student: This is a cat with a ball.
    Teacher gives marks to the student's answer only in numbers within range of 1 and 8.
    The marks: 3

    Example 3:
    Teacher: He has a dog.
    Student: He had a dog.
    Teacher gives marks to the student's answer only in numbers within range of 1 and 5.
    The marks: 4

    Example 4:
    Teacher: He has a red shirt.
    Student: He has a red shirt.
    Teacher gives marks to the student's answer only in numbers within range of 1 and 5.
    The marks: 5

    Example 5:
    Teacher: That is a bull.
    Student: That is a cow.
    Teacher gives marks to the student's answer only in numbers within range of 1 and 5.
    The marks: 1
    """

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


# Cosine similarity
    
def get_embedding(text, model="gpt-4-32k"):
    return openai.Embedding.create(engine=model, input=[text])['data'][0]['embedding']

