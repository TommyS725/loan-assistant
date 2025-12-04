from rag import RAG
from sqlite3 import Connection as SQLiteConnection
from langchain.tools import BaseTool, tool
import dal
import model


def calc_apr(
    principal: float, monthly_payment: float, term_months: int, fee: float = 0.0
):
    n = term_months
    P = principal - fee
    L = monthly_payment
    # Using Newton-Raphson method to approximate monthly rate
    v = 0.1  # initial guess
    epsilon = 1e-6
    for _ in range(50):
        prev = v
        fv = P * (1 + v) ** n - L * ((1 + v) ** n - 1) / v
        fprime = P * n * (1 + v) ** (n - 1) - (L / (v**2)) * (
            v * n * (1 + v) ** (n - 1) - ((1 + v) ** n - 1)
        )
        v = v - fv / fprime
        if abs(v - prev) < epsilon:
            break

    APR = (1 + v) ** 12 - 1
    return APR * 100  # return as percentage


def get_tools(rag: RAG, db_conn: SQLiteConnection) -> list[BaseTool]:
    # rag tools
    @tool(
        "retrieve_loan_knowledge",
        description="Use this tool to retrieve relevant loan documents and information to assist with user queries about loans.",
    )
    def retrieve_loan_knowledge(query: str) -> str:
        try:
            docs = rag.search(query, k=3)
            print(f"Retrieved {len(docs)} documents for query")
            combined_content = "\n\n".join([doc.page_content for doc in docs])
            return (
                combined_content if combined_content else "No relevant documents found."
            )
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return "No relevant documents found due to an error."

    # db tools
    @tool(
        "get_user_loans",
        description="Use this tool to get the existing loans of a user by their user ID.",
    )
    def get_user_loans_tool(user_id: int) -> str:
        loans = dal.get_user_loans(db_conn, user_id)
        return (
            model.user_loan_list_to_context(loans)
            if loans
            else "No loans found for this user."
        )

    @tool(
        "get_available_loans",
        description="Use this tool to get the list of available loans.",
    )
    def get_available_loans_tool() -> str:
        loans = dal.get_available_loans(db_conn)
        return (
            "".join([loan.to_context() for loan in loans])
            if loans
            else "No available loans found."
        )

    @tool(
        "get_specific_loan",
        description="Use this tool to get details of a specific loan by its loan ID.",
    )
    def get_specific_loan_tool(loan_id: int) -> str:
        loan = dal.get_specific_loan(db_conn, loan_id)
        if loan:
            return loan.to_context()
        else:
            return "Loan not found."

    # calculation tools can be added here

    @tool(
        "calculate_Annual_Percentage_Rate",
        description="Use this tool to calculate the Annual Percentage Rate (APR) given principal, fee, monthly payment and term in months.",
    )
    def calculate_APR(
        principal: float, monthly_payment: float, term_months: int, fee: float = 0.0
    ) -> str:
        apr = calc_apr(principal, monthly_payment, term_months, fee)
        return str(apr)

    @tool(
        "multiple_apr_calculator",
        description="Use this tool to calculate APR for multiple loans.",
    )
    def multiple_apr_calculator(
        principals: list[float],
        monthly_payments: list[float],
        term_months_list: list[int],
        fees: list[float] | None = None,
    ) -> str:
        if not fees:
            fees = [0.0] * len(principals)
        aprs = []
        for principal, monthly_payment, term_months, fee in zip(
            principals, monthly_payments, term_months_list, fees
        ):
            apr = calc_apr(principal, monthly_payment, term_months, fee)
            aprs.append(apr)
        return str(aprs)

    @tool(
        "general_calculation_tool",
        description="Use this tool to perform general  calculations based on provided expression.",
    )
    def general_calculation_tool(expression: str) -> str:
        # A simple eval-based calculator (ensure safety in real implementations)
        try:
            return str(eval(expression))
        except Exception as e:
            return f"Error in calculation: {e}"

    @tool(
        "batch_general_calculation_tool",
        description="Use this tool to perform batch general calculations based on provided expressions.",
    )
    def batch_general_calculation_tool(expressions: list[str]) -> str:
        results = []
        for expression in expressions:
            try:
                result = eval(expression)
                results.append(result)
            except Exception as e:
                results.append(f"Error in calculation: {e}")
        return str(results)

    return [
        retrieve_loan_knowledge,
        get_user_loans_tool,
        get_available_loans_tool,
        get_specific_loan_tool,
        calculate_APR,
        multiple_apr_calculator,
        general_calculation_tool,
        batch_general_calculation_tool,
    ]
