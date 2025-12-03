from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_community.utilities.sql_database import SQLDatabase
import sqlite3
from datetime import datetime, timedelta
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any


def create_database(db_path: str = "loans_demo.db"):
    """Create database with the given schema"""
    # Allow connections to be used across threads where necessary by enabling
    # check_same_thread=False. Individual threads should still avoid sharing
    # cursors concurrently, but this prevents the common Streamlit threading
    # error when using ThreadPoolExecutor or similar.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        monthly_payment REAL NOT NULL,
        interest_rate REAL NOT NULL,
        term_months INTEGER NOT NULL,
        fee REAL NOT NULL,      
        description TEXT NOT NULL,
        required_credit_score INTEGER NOT NULL,
        requirement_income REAL NOT NULL,
        other_requirements TEXT NOT NULL
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        email TEXT NOT NULL,
        credit_score INTEGER NOT NULL,
        income REAL NOT NULL,
        job_title TEXT NOT NULL,
        other_info TEXT NOT NULL
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS user_loans (
        application_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        loan_id INTEGER NOT NULL,
        applied_on TEXT NOT NULL,
        ended BOOLEAN DEFAULT 0,
        record TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (loan_id) REFERENCES loans (loan_id)
    )
    """
    )

    conn.commit()
    return conn


def seed_loans(cursor: sqlite3.Cursor):
    """Seed loan products with different requirements and monthly payments"""

    def calculate_monthly_payment(amount, interest_rate, term_months):
        """Calculate monthly payment using amortization formula"""
        monthly_rate = interest_rate / 100 / 12
        if monthly_rate == 0:
            return amount / term_months
        payment = amount * monthly_rate * (1 + monthly_rate) ** term_months
        payment /= (1 + monthly_rate) ** term_months - 1
        return round(payment, 2)

    loan_data = [
        # Personal Loan
        {
            "loan_id": 1,
            "type": "Personal",
            "amount": 10000.0,
            "interest_rate": 5.5,
            "term_months": 24,
            "fee": 100.0,
            "description": "Unsecured personal loan for various purposes",
            "required_credit_score": 650,
            "requirement_income": 30000.0,
            "other_requirements": "Minimum 2 years of employment history",
        },
        # Mortgage
        {
            "loan_id": 2,
            "type": "Mortgage",
            "amount": 300000.0,
            "interest_rate": 4.2,
            "term_months": 360,
            "fee": 2000.0,
            "description": "Home mortgage loan for first-time buyers",
            "required_credit_score": 700,
            "requirement_income": 80000.0,
            "other_requirements": "20% down payment required, property appraisal needed",
        },
        # Auto Loan
        {
            "loan_id": 3,
            "type": "Auto",
            "amount": 25000.0,
            "interest_rate": 4.8,
            "term_months": 60,
            "fee": 150.0,
            "description": "Auto loan for new or used vehicles",
            "required_credit_score": 600,
            "requirement_income": 35000.0,
            "other_requirements": "Vehicle must be less than 10 years old",
        },
        # Small Business Loan
        {
            "loan_id": 4,
            "type": "Small Business",
            "amount": 50000.0,
            "interest_rate": 6.5,
            "term_months": 48,
            "fee": 500.0,
            "description": "Loan for small business expansion",
            "required_credit_score": 720,
            "requirement_income": 100000.0,
            "other_requirements": "Business plan required, minimum 2 years in business",
        },
        # Student Loan
        {
            "loan_id": 5,
            "type": "Student",
            "amount": 20000.0,
            "interest_rate": 3.5,
            "term_months": 120,
            "fee": 50.0,
            "description": "Student loan for education expenses",
            "required_credit_score": 580,
            "requirement_income": 20000.0,
            "other_requirements": "Must be currently a student in accredited institution",
        },
        # Emergency Medical Loan
        {
            "loan_id": 6,
            "type": "Emergency Medical",
            "amount": 15000.0,
            "interest_rate": 7.2,
            "term_months": 36,
            "fee": 75.0,
            "description": "Loan for unexpected medical expenses",
            "required_credit_score": 620,
            "requirement_income": 25000.0,
            "other_requirements": "Medical bills verification required, health insurance not mandatory",
        },
        # Home Improvement Loan
        {
            "loan_id": 7,
            "type": "Home Improvement",
            "amount": 35000.0,
            "interest_rate": 5.8,
            "term_months": 84,
            "fee": 250.0,
            "description": "Loan for home renovations and improvements",
            "required_credit_score": 680,
            "requirement_income": 60000.0,
            "other_requirements": "Homeowner required, contractor estimate needed",
        },
        # Debt Consolidation Loan
        {
            "loan_id": 8,
            "type": "Debt Consolidation",
            "amount": 25000.0,
            "interest_rate": 6.0,
            "term_months": 48,
            "fee": 200.0,
            "description": "Consolidate high-interest debts into one payment",
            "required_credit_score": 670,
            "requirement_income": 45000.0,
            "other_requirements": "Existing debt statements required, no recent bankruptcies",
        },
    ]

    # Calculate and add monthly_payment to each loan
    loans = []
    for loan in loan_data:
        monthly_payment = calculate_monthly_payment(
            loan["amount"], loan["interest_rate"], loan["term_months"]
        )

        loans.append(
            {
                "loan_id": loan["loan_id"],
                "type": loan["type"],
                "amount": loan["amount"],
                "monthly_payment": monthly_payment,
                "interest_rate": loan["interest_rate"],
                "term_months": loan["term_months"],
                "fee": loan["fee"],
                "description": loan["description"],
                "required_credit_score": loan["required_credit_score"],
                "requirement_income": loan["requirement_income"],
                "other_requirements": loan["other_requirements"],
            }
        )

    cursor.executemany(
        """
    INSERT INTO loans VALUES (
        :loan_id, :type, :amount, :monthly_payment, :interest_rate, :term_months, :fee, 
        :description, :required_credit_score, :requirement_income, :other_requirements
    )
    """,
        loans,
    )


def seed_users(cursor: sqlite3.Cursor):
    """Seed users with different financial profiles and other_info"""
    users = [
        # User 1 - Young Professional (needs personalized suggestions)
        {
            "user_id": 1,
            "email": "young.professional@example.com",
            "credit_score": 720,
            "income": 68000.0,
            "job_title": "Marketing Manager",
            "other_info": "Working at advertising agency for 3 years and 2 months. Previously interned for 6 months. Renting apartment in downtown. Owns 2018 Honda Civic. No criminal record. Has $15k in student loan debt. Looking to consolidate debt and potentially buy first car upgrade.",
        },
        # User 2 - Unemployed but with assets (rejection case - no income)
        {
            "user_id": 2,
            "email": "unemployed.asset@example.com",
            "credit_score": 620,
            "income": 0.0,
            "job_title": "Unemployed",
            "other_info": "Recently laid off from tech job after 4 years and 3 months at Google as Senior Software Engineer. Owns 2019 Tesla Model 3. Has significant savings ($100k). No criminal record. Currently on severance package for 6 months.",
        },
        # User 3 - Seasonal Worker with DUI (rejection case - low income + criminal)
        {
            "user_id": 3,
            "email": "seasonal.worker@example.com",
            "credit_score": 590,
            "income": 28000.0,
            "job_title": "Seasonal Construction Worker",
            "other_info": "Works construction April-October for 5 years. Unemployed November-March. Previously worked 2 years as warehouse worker. Owns pickup truck: 2015 Ford F-150. Previous DUI conviction 3 years ago (completed probation). Tools and equipment valued at $15k.",
        },
        # User 4 - First-time Home Buyer (mortgage success case)
        {
            "user_id": 4,
            "email": "first.home@example.com",
            "credit_score": 710,
            "income": 85000.0,
            "job_title": "Data Scientist",
            "other_info": "Works at tech startup TechCorp for 2 years and 3 months. Previously interned at IBM for 6 months. Renting apartment, saving for down payment. Owns 2019 Subaru Forester. No criminal record. Has $60k saved for down payment (20% of $300k). Stable employment history.",
        },
        # User 5 - Small Business Owner (business loan success)
        {
            "user_id": 5,
            "email": "small.business@example.com",
            "credit_score": 740,
            "income": 110000.0,
            "job_title": "Small Business Owner",
            "other_info": "Owns a boutique coffee shop for 3 years and 1 month. Previously managed Starbucks for 5 years. Business revenue $300k annually. Owns delivery van: 2020 Ford Transit. No criminal record. Business has 5 employees. Looking to expand to second location.",
        },
        # User 6 - Medical Resident (borderline but promising success)
        {
            "user_id": 6,
            "email": "medical.resident@example.com",
            "credit_score": 710,
            "income": 55000.0,
            "job_title": "Medical Resident",
            "other_info": "Third year resident at Johns Hopkins for 2 years and 9 months. Previously completed 4 years of medical school. High future earning potential. Owns 2016 Honda Accord. Student loan debt $200k (deferred during residency). No criminal record. Works 80-hour weeks.",
        },
        # User 7 - Student with part-time job (student loan success)
        {
            "user_id": 7,
            "email": "student.borrower@example.com",
            "credit_score": 680,
            "income": 15000.0,
            "job_title": "Student",
            "other_info": "Full-time MBA student at Stanford. Part-time internship at Google for 8 months. Previously worked 2 years as Business Analyst at McKinsey. Owns 2015 Honda Civic. No criminal record. Scholarship covers 70% of tuition. Living in student housing.",
        },
        # User 8 - Recent Graduate (auto loan success)
        {
            "user_id": 8,
            "email": "new.grad@example.com",
            "credit_score": 670,
            "income": 70000.0,
            "job_title": "Software Engineer I",
            "other_info": "Graduated 6 months ago from MIT. Currently working at Google for 6 months. Previously interned at Microsoft for 3 months. Renting apartment. No vehicle (uses public transit). Student loan debt $40k. No criminal record. Building credit history.",
        },
        # User 9 - Remote Worker (multiple loan success)
        {
            "user_id": 9,
            "email": "digital.nomad@example.com",
            "credit_score": 730,
            "income": 85000.0,
            "job_title": "Remote Software Developer",
            "other_info": "Works remotely for tech company GitLab for 3 years and 7 months. Previously worked 2 years at Facebook office. Travels internationally frequently. No permanent address. Owns laptop and camera gear. No vehicle ownership. No criminal record. Uses co-working spaces globally.",
        },
        # User 10 - Freelancer/Contractor (personal loan success)
        {
            "user_id": 10,
            "email": "freelancer.designer@example.com",
            "credit_score": 690,
            "income": 65000.0,
            "job_title": "Freelance Graphic Designer",
            "other_info": "Self-employed for 3 years and 2 months. Previously worked 4 years as Graphic Designer at Adobe. Variable monthly income but consistent yearly average. Owns 2021 MacBook Pro, professional camera equipment. No vehicle ownership (uses car-sharing). No criminal record.",
        },
        # User 11 - Gig worker (auto loan for work vehicle success)
        {
            "user_id": 11,
            "email": "gig.worker@example.com",
            "credit_score": 610,
            "income": 32000.0,
            "job_title": "Ride-share Driver",
            "other_info": "Drives for Uber and Lyft full-time for 2 years and 8 months. Previously worked 3 years as delivery driver for Amazon. Owns 2018 Toyota Prius (used for work). Previous minor traffic violations (2 speeding tickets). Works 50+ hours weekly. Income varies by season.",
        },
        # User 12 - Retired (personal + auto loan success)
        {
            "user_id": 12,
            "email": "retired.teacher@example.com",
            "credit_score": 750,
            "income": 45000.0,
            "job_title": "Retired Teacher",
            "other_info": "Retired after 30 years and 6 months of teaching at Lincoln High School. Pension income stable. Owns home outright (no mortgage). Has 2 vehicles: 2017 Toyota Camry and 2020 Honda CR-V. No criminal record. Travels frequently.",
        },
        # User 13 - Stay-at-home parent (rejection - needs joint application)
        {
            "user_id": 13,
            "email": "stay.home.parent@example.com",
            "credit_score": 720,
            "income": 0.0,
            "job_title": "Stay-at-Home Parent",
            "other_info": "Manages household. Previously worked as accountant for 8 years and 4 months at Deloitte. Joint assets with spouse. Owns 2019 minivan (Honda Odyssey). No criminal record. Volunteer work at local school for 2 years.",
        },
    ]
    cursor.executemany(
        """
    INSERT INTO users VALUES (
        :user_id, :email, :credit_score, :income, :job_title, :other_info
    )
    """,
        users,
    )


def seed_user_loans(cursor: sqlite3.Cursor):
    """Seed only successful loan applications"""
    applications = []
    application_id = 1

    # Define some application dates
    base_date = datetime.now() - timedelta(days=90)

    # USER 1 - Young Professional (Only 1 successful loan - for demo purposes)
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 1,
                "loan_id": 1,  # Personal Loan
                "applied_on": (base_date + timedelta(days=5)).isoformat(),
                "ended": False,
                "record": "Personal loan approved for debt consolidation. Good credit score and stable employment history. $15k student debt manageable with current income.",
            },
        ]
    )
    application_id += 1

    # User 4 (First-time Home Buyer) - Mortgage
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 4,
                "loan_id": 2,
                "applied_on": (base_date + timedelta(days=20)).isoformat(),
                "ended": False,
                "record": "Mortgage approved for first home purchase. 20% down payment secured. Income meets requirement. Stable employment at tech startup. Good debt-to-income ratio.",
            }
        ]
    )
    application_id += 1

    # User 5 (Small Business Owner) - Small Business Loan
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 5,
                "loan_id": 4,
                "applied_on": (base_date + timedelta(days=25)).isoformat(),
                "ended": False,
                "record": "Small business loan approved for expansion. Business revenue verified through tax returns. 3-year business history meets requirement. Business plan approved by committee.",
            }
        ]
    )
    application_id += 1

    # User 6 (Medical Resident) - Personal Loan
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 6,
                "loan_id": 1,
                "applied_on": (base_date + timedelta(days=30)).isoformat(),
                "ended": False,
                "record": "Personal loan approved. Medical resident with high future earning potential. Stable hospital income meets requirements. Professional license enhances credibility.",
            }
        ]
    )
    application_id += 1

    # User 7 (Student) - Student Loan
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 7,
                "loan_id": 5,
                "applied_on": (base_date + timedelta(days=35)).isoformat(),
                "ended": False,
                "record": "Student loan approved. Enrolled at Stanford University (accredited institution). Part-time income meets requirement. Excellent academic standing.",
            }
        ]
    )
    application_id += 1

    # User 8 (Recent Graduate) - Auto Loan
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 8,
                "loan_id": 3,
                "applied_on": (base_date + timedelta(days=40)).isoformat(),
                "ended": False,
                "record": "Auto loan approved for first vehicle. New job at Google provides stable income. MIT graduate status favorable. Building credit history, co-signer not required.",
            }
        ]
    )
    application_id += 1

    # User 9 (Remote Worker) - Personal and Auto Loans
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 9,
                "loan_id": 1,
                "applied_on": (base_date + timedelta(days=45)).isoformat(),
                "ended": False,
                "record": "Personal loan approved. Stable remote work income verified. Excellent credit score. International travel history not a concern for unsecured loan.",
            },
            {
                "application_id": application_id + 1,
                "user_id": 9,
                "loan_id": 3,
                "applied_on": (base_date + timedelta(days=50)).isoformat(),
                "ended": False,
                "record": "Auto loan approved (decided to purchase vehicle for domestic travel). High income meets requirements. No criminal record. Digital nomad lifestyle accommodated.",
            },
        ]
    )
    application_id += 2

    # User 10 (Freelancer) - Personal Loan
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 10,
                "loan_id": 1,
                "applied_on": (base_date + timedelta(days=55)).isoformat(),
                "ended": False,
                "record": "Personal loan approved. Freelance income verified through bank statements (3-year history). Credit score meets requirement. No criminal record favorable.",
            }
        ]
    )
    application_id += 1

    # User 11 (Gig worker) - Auto Loan
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 11,
                "loan_id": 3,
                "applied_on": (base_date + timedelta(days=60)).isoformat(),
                "ended": False,
                "record": "Auto loan approved for vehicle upgrade. Income from ride-sharing verified. Vehicle essential for livelihood. Interest rate adjusted for risk profile.",
            }
        ]
    )
    application_id += 1

    # User 12 (Retired) - Personal and Auto Loans
    applications.extend(
        [
            {
                "application_id": application_id,
                "user_id": 12,
                "loan_id": 1,
                "applied_on": (base_date + timedelta(days=65)).isoformat(),
                "ended": True,
                "record": "Personal loan approved. Stable pension income meets requirement. Excellent credit history. Home ownership with no mortgage strengthens application.",
            },
            {
                "application_id": application_id + 1,
                "user_id": 12,
                "loan_id": 3,
                "applied_on": (base_date + timedelta(days=70)).isoformat(),
                "ended": False,
                "record": "Auto loan approved for new vehicle purchase. Existing vehicles to be traded in. Pension income sufficient for payments. Excellent payment history on previous auto loans.",
            },
        ]
    )

    cursor.executemany(
        """
    INSERT INTO user_loans VALUES (
        :application_id, :user_id, :loan_id, :applied_on, :ended, :record
    )
    """,
        applications,
    )


def init_db(db_path: str = "loans_demo.db"):
    db_exist = os.path.exists(db_path)
    if not db_exist:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = create_database(db_path)
    if not db_exist:
        cursor = conn.cursor()
        seed_loans(cursor)
        seed_users(cursor)
        seed_user_loans(cursor)
        conn.commit()
    # Create an engine that creates new sqlite connections per SQLAlchemy
    # connection request. Use check_same_thread=False for thread usage.
    engine = create_engine(
        "sqlite://",
        creator=lambda: sqlite3.connect(db_path, check_same_thread=False),
    )
    db = SQLDatabase(engine)
    return conn, db
