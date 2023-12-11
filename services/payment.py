from fastapi import APIRouter, Request, Depends, HTTPException, Header, Body
from starlette import status
from bson import ObjectId
from starlette.responses import RedirectResponse
from database.transactions import TransactionsDB
from models.payment import CreateCheckoutSession, CheckTransaction
from models.user import TempUserBase
from utils.user import (
    get_current_active_user,
    is_admin,
    get_hashed_password,
)
from database.user import UserDB
# import stripe
import uuid
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from phonepe.sdk.pg.env import Env
import datetime


# [PhonePe] This is for test
MERCHANT_ID = "PGTESTPAYUAT"
SALT_KEY = "099eb0cd-02cf-4e2a-8aca-3e6c6aff0399"
SALT_INDEX = 1

env = Env.UAT
should_publish_events = True
phonepe_client = PhonePePaymentClient(MERCHANT_ID, SALT_KEY, SALT_INDEX, env, should_publish_events)


# PAYMENT_DOMAIN = 'http://localhost:5173/login/'
# BACKEND_DOMAIN = 'http://localhost:8000/payment/callback'
PAYMENT_DOMAIN = 'https://tutor-swan.com/login/'
BACKEND_DOMAIN = 'https://tutorswan-backend.onrender.com/payment/callback'

router = APIRouter()
user_db = UserDB()
transaction_db = TransactionsDB()


def calculate_total_price(num_students, plan_price, num_subjects, num_semesters):
    # Your logic to calculate total price
    total_price = num_students * plan_price * num_subjects * num_semesters
    return total_price

def get_plan_details(num_students):
    # Your logic to determine the plan based on the number of students
    if num_students <= 300:
        return "Basic", 35
    elif 301 <= num_students <= 600:
        return "Startup", 30
    else:
        return "Premium", 25
    

@router.post('/create-checkout-session')
def create_checkout_session(
    data: TempUserBase, 
):

    plan_name, plan_price = get_plan_details(data.nosStudents)
    # Calculate total price
    total_price = calculate_total_price(data.nosStudents, plan_price , data.nosSubjects, data.nosSemesters)
    total_credits = data.nosStudents * data.nosSubjects * data.nosSemesters

    # max transaction_id will be 38 characters long
    transaction_id = str(uuid.uuid4())[:28]
    transaction_id = str(transaction_id + "0x1240" + str(total_credits))

    temp_user_id = user_db.create_temp_user({
        "name": data.name,
        "instituteName": data.instituteName,
        "userName": data.userName,
        "email": data.email,
        "password": get_hashed_password(data.password),
        "nosStudents": data.nosStudents,
        "nosSemesters": data.nosSemesters,
        "nosSubjects": data.nosSubjects,
        "plan": plan_name,
        "total_credits": total_credits,
        "transaction_id": transaction_id,
        "created_at": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    })
    print(temp_user_id)

    try:

        PAISA = 100 # 1 Rupee = 100 Paisa

        pay_page_request =  PgPayRequest.pay_page_pay_request_builder(
                                merchant_transaction_id = transaction_id,
                                amount=total_price*PAISA,
                                merchant_user_id=str(temp_user_id),
                                callback_url=BACKEND_DOMAIN,
                                redirect_url=PAYMENT_DOMAIN + '?check=true&transaction_id=' + transaction_id,
                                merchant_order_id=temp_user_id,
                            )
        pay_page_response = phonepe_client.pay(pay_page_request)
        pay_page_url = pay_page_response.data.instrument_response.redirect_info.url

        return {"url": pay_page_url}
    except Exception as e:
        print(e)
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/verify-payment")
async def verify_payment(
    transaction_id: CheckTransaction,
):
    
    response = phonepe_client.check_status(transaction_id.transaction_id)
    if response.success:
        print("\nPayment verification successful")

        temp_user_details = user_db.get_temp_user_transaction_id(transaction_id.transaction_id)
        user_db.create_user({
            "name": temp_user_details["name"],
            "instituteName": temp_user_details["instituteName"],
            "userName": temp_user_details["userName"],
            "email": temp_user_details["email"],
            "password": temp_user_details["password"],
            "role": "teacher",
            "plan": temp_user_details["plan"],
            "total_credits": temp_user_details["total_credits"],
            "subjects": [],
            "created_at": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        })

        if temp_user_details:
            user_db.delete_temp_user(temp_user_details["_id"])

        return {"success": True, "message": "Payment verification successful"}
    
    else:
        print("\nPayment verification failed\n")
        raise HTTPException(status_code=400, detail="Payment verification failed")
    

@router.get("/admin/transactions/{limit}/{id}")
async def get_transactions(
    limit: int = 10,
    id: str = None,
    current_user: ObjectId = Depends(is_admin)
):
    transactions = transaction_db.get_transactions(limit, id)
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")
    return transactions


@router.get("/user/transactions/{limit}/{id}")
async def get_user_transactions(
    limit: int = 10,
    id: str = None,
    current_user: ObjectId = Depends(get_current_active_user)
):
    transactions = transaction_db.get_transaction_by_user_id(current_user['_id'], limit, id)
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")
    return transactions

@router.post("/callback")
async def callback(
    x_verify: str = Header(None),
    response_data: dict = Body(None),
):
    response_data_str = str(response_data)
    response_data_str = response_data_str.replace("\'", "\"")
    # print("\nCallback called")
    # print("x_verify: ", x_verify)
    # print("response_data: ", response_data_str)
    # print("\n")
    # Convert the response_data dict to a JSON string

    # Perform PhonePe callback verification
    is_valid = phonepe_client.verify_response(x_verify=x_verify, response=response_data_str)

    # Check the validity and return the result
    if is_valid:
        print("\nCallback verification successful")

        return {"message": "Callback verification successful"}
    else:
        print("\nCallback verification failed\n")
        raise HTTPException(status_code=400, detail="Callback verification failed")


# @router.post('/create-portal-session')
# def customer_portal(session_id: str = Form(...)):
#     checkout_session = stripe.checkout.Session.retrieve(session_id)
#     return_url = PAYMENT_DOMAIN

#     portal_session = stripe.billing_portal.Session.create(
#         customer=checkout_session.customer,
#         return_url=return_url,
#     )
#     return RedirectResponse(portal_session.url, status_code=303)

