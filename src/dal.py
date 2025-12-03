from sqlite3 import Connection as SQLiteConnection
from model import Loan, User, UserLoan, UserLoanWithDetails


def get_available_loans(db_conn: SQLiteConnection) -> list[Loan]:
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM loans")
    rows = cursor.fetchall()
    loans = [
        Loan(**dict(zip([column[0] for column in cursor.description], row)))
        for row in rows
    ]
    return loans


def get_user_loans(
    db_conn: SQLiteConnection, user_id: int
) -> list[UserLoanWithDetails]:
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT * FROM user_loans INNER JOIN loans ON user_loans.loan_id = loans.loan_id WHERE user_loans.user_id = ?",
        (user_id,),
    )
    rows = cursor.fetchall()
    user_loans = []
    for row in rows:
        row_dict = dict(zip([column[0] for column in cursor.description], row))
        loan = Loan(
            type=row_dict["type"],
            loan_id=row_dict["loan_id"],
            interest_rate=row_dict["interest_rate"],
            term_months=row_dict["term_months"],
            monthly_payment=row_dict["monthly_payment"],
            amount=row_dict["amount"],
            description=row_dict["description"],
            fee=row_dict["fee"],
            required_credit_score=row_dict["required_credit_score"],
            requirement_income=row_dict["requirement_income"],
            other_requirements=row_dict["other_requirements"],
        )
        user_loan = UserLoanWithDetails(
            application_id=row_dict["application_id"],
            user_id=row_dict["user_id"],
            loan_id=row_dict["loan_id"],
            applied_on=row_dict["applied_on"],
            ended=row_dict["ended"],
            record=row_dict["record"],
            loan_details=loan,
        )
        user_loans.append(user_loan)
    return user_loans


def get_specific_loan(db_conn: SQLiteConnection, loan_id: int) -> Loan | None:
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM loans WHERE loan_id = ?", (loan_id,))
    row = cursor.fetchone()
    if row:
        loan = Loan(**dict(zip([column[0] for column in cursor.description], row)))
        return loan
    return None


def add_user_loan_record(
    db_conn: SQLiteConnection, user_id: int, loan_id: int, record: str
) -> None:
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO user_loans (user_id, loan_id, applied_on, ended, record) VALUES (?, ?, DATE('now'), 0, ?)",
        (user_id, loan_id, record),
    )
    db_conn.commit()


def get_users(db_conn: SQLiteConnection) -> list[User]:
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    users = [
        User(**dict(zip([column[0] for column in cursor.description], row)))
        for row in rows
    ]
    return users


def get_user_by_id(db_conn: SQLiteConnection, user_id: int) -> User | None:
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        user = User(**dict(zip([column[0] for column in cursor.description], row)))
        return user
    return None
