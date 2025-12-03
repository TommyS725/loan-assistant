from pydantic import BaseModel, Field


class Loan(BaseModel):
    loan_id: int = Field(..., description="Unique identifier for the loan")
    type: str = Field(
        ..., description="The type of the loan (e.g., personal, mortgage)"
    )
    amount: float = Field(..., description="The amount of the loan")
    monthly_payment: float = Field(
        ..., description="The monthly payment amount for the loan"
    )
    interest_rate: float = Field(..., description="The interest rate of the loan")
    term_months: int = Field(..., description="The term of the loan in months")
    fee: float = Field(..., description="The fee associated with the loan")
    description: str = Field(..., description="A brief description of the loan")
    # requirement
    required_credit_score: int = Field(
        ..., description="The required credit score for the loan"
    )
    requirement_income: float = Field(
        ..., description="The required annual income for the loan"
    )
    other_requirements: str = Field(
        ..., description="Other requirements for the loan in text format"
    )

    def to_context(self) -> str:
        return (
            f"Loan Details:\n"
            f"- Loan ID: {self.loan_id}\n"
            f"- Type: {self.type}\n"
            f"- Amount: {self.amount}\n"
            f"- Monthly Payment: {self.monthly_payment}\n"
            f"- Interest Rate: {self.interest_rate}\n"
            f"- Term (months): {self.term_months}\n"
            f"- Fee: {self.fee}\n"
            f"- Description: {self.description}\n"
            f"- Required Credit Score: {self.required_credit_score}\n"
            f"- Required Income: {self.requirement_income}\n"
            f"- Other Requirements: {self.other_requirements}\n"
        )


class User(BaseModel):
    user_id: int = Field(..., description="Unique identifier for the user")
    email: str = Field(..., description="The email address of the user")
    credit_score: int = Field(..., description="The credit score of the user")
    income: float = Field(..., description="The annual income of the user")
    job_title: str = Field(..., description="The job title of the user")
    other_info: str = Field(
        ..., description="Other relevant information about the user"
    )

    def to_context(self) -> str:
        return (
            f"User Profile:\n"
            f"- User ID: {self.user_id}\n"
            f"- Email: {self.email}\n"
            f"- Credit Score: {self.credit_score}\n"
            f"- Income: {self.income}\n"
            f"- Job Title: {self.job_title}\n"
            f"- Other Info: {self.other_info}\n"
        )


class UserLoan(BaseModel):
    application_id: int = Field(
        ..., description="Unique identifier for the application"
    )
    user_id: int = Field(..., description="The ID of the user applying for the loan")
    loan_id: int = Field(..., description="The ID of the loan being applied for")
    applied_on: str = Field(
        ..., description="The date when the application was submitted"
    )
    ended: bool = Field(
        False, description="Indicates whether the loan period has ended"
    )
    record: str = Field(..., description="The application record in text format")

    def to_context(self) -> str:
        return (
            f"User Loan Application:\n"
            f"- Application ID: {self.application_id}\n"
            f"- User ID: {self.user_id}\n"
            f"- Loan ID: {self.loan_id}\n"
            f"- Applied On: {self.applied_on}\n"
            f"- Ended: {self.ended}\n"
            f"- Record: {self.record}\n"
        )


class UserLoanWithDetails(UserLoan):
    loan_details: Loan = Field(..., description="Detailed information about the loan")

    def to_context(self) -> str:
        lines = []
        base_context = super().to_context()
        lines += base_context.splitlines()[1:]  # skip first line
        lines += self.loan_details.to_context().splitlines()[1:]  # skip first line
        return "\n".join(lines)


def user_loan_list_to_context(user_loans: list[UserLoanWithDetails]) -> str:
    if not user_loans:
        return "No existing loans."
    res = []
    for i, ul in enumerate(user_loans, start=1):
        res.append(f"--- Loan {i} ---\n{ul.to_context()}")
    return "\n".join(res)


class BaseAgentOutputSchema(BaseModel):
    response: str = Field(..., description="The agent's response message to the user.")
    loan_id_to_apply: int | None = Field(
        None, description="The loan ID the user wants to apply for, if any."
    )


base_agent_output_res_example = BaseAgentOutputSchema.model_validate(
    {
        "response": "You have applied for 5 personal loan, 2 mortgage loan. Please tell me if you want to check the details.",
        "loan_id_to_apply": None,
    }
).model_dump_json()
base_agent_output_apply_example = BaseAgentOutputSchema.model_validate(
    {
        "response": "",
        "loan_id_to_apply": 3,
    }
).model_dump_json()


class EligibilityAgentOutputSchema(BaseModel):
    application_eligible: bool = Field(
        ..., description="Indicates if the user's application is eligible for the loan."
    )
    assessment_record: str = Field(
        ..., description="Detailed record of the eligibility assessment."
    )
    user_message: str = Field(
        ...,
        description="Message to be conveyed to the user regarding their application.",
    )


eligibility_agent_output_success_example = EligibilityAgentOutputSchema.model_validate(
    {
        "application_eligible": True,
        "assessment_record": "The user meets all the eligibility criteria for the loan by having a credit score of 750 and an annual income of $85,000, which exceed the required thresholds.",
        "user_message": "Congratulations! Your application for the loan (ID:5) has been approved based on your credit score and income.",
    }
).model_dump_json()
eligibility_agent_output_reject_example = EligibilityAgentOutputSchema.model_validate(
    {
        "application_eligible": False,
        "assessment_record": "The user's application was rejected due to a credit score of 600, which is below the required minimum of 650 for this loan.",
        "user_message": "We regret to inform you that your application for the loan has been rejected due to not meeting the required credit score criteria.",
    }
).model_dump_json()
