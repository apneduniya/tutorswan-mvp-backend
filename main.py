from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from routers import user, subjects, paper_pattern
from services import payment
from database.connection import DBConnection
from database.database import (MONGO_CONNECTION_URL, DATABASE_NAME)
import os


app = FastAPI(
#    docs_url=None, # Disable docs (Swagger UI)
#    redoc_url=None, # Disable redoc
    title="TutorSwan API",
    description="API for TutorSwan",
    version="1.0.0",
)

# Set the allowed origins, methods, headers, and other CORS options
# origins = [
#     "http://localhost",
#     "http://localhost:3000",
# ]
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/user")
app.include_router(subjects.router, prefix="/subjects")
app.include_router(paper_pattern.router, prefix="/paper-pattern")

app.include_router(payment.router, prefix="/payment")

# Create an instance of DBConnection
db_connection = DBConnection(MONGO_CONNECTION_URL, DATABASE_NAME)

def create_directory_if_not_exists():
    current_directory = os.getcwd()
    final_directory = os.path.join(current_directory, r'uploads')
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)
        print(f"Directory /uploads created.")
    else:
        print(f"Directory /uploads already exists.")

# Example usage:


@app.on_event("startup")
async def startup_event():
    db_connection.connect()
    print("\nS E R V E R   S T A R T I N G . . . . . . . . . .\n")


@app.on_event("shutdown")
async def shutdown_event():
    db_connection.disconnect()
    print("\nS E R V E R   S H U T D O W N . . . . . . . . . .\n")


