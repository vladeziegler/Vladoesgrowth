from crewai_tools import BaseTool
from enum import Enum
from typing import Optional, Type
from pydantic import BaseModel, Field

class Operation(str, Enum):
    """Available operations"""
    ADD = "add"
    SUBTRACT = "subtract"

class CalculationToolInput(BaseModel):
    """Schema for calculation tool input"""
    first_number: float = Field(
        description="The first number in the calculation"
    )
    second_number: float = Field(
        description="The second number in the calculation"
    )
    operation: Operation = Field(
        description="The operation to perform (add or subtract)"
    )

class CalculationToolOutput(BaseModel):
    """Schema for calculation tool output"""
    result: float = Field(
        description="The result of the calculation"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if any"
    )

class CalculationTool(BaseTool):
    name: str = "CalculationTool"
    description: str = """Useful for when you need to calculate costs by adding or subtracting numbers."""
    args_schema: Type[BaseModel] = CalculationToolInput

    def _run(self, first_number: float, second_number: float, operation: str) -> str:
        try:
            print(f"Calculating: {first_number} {operation} {second_number}")
            
            # Create input model and validate
            tool_input = CalculationToolInput(
                first_number=first_number,
                second_number=second_number,
                operation=operation
            )
            
            if tool_input.operation == Operation.ADD:
                result = tool_input.first_number + tool_input.second_number
            elif tool_input.operation == Operation.SUBTRACT:
                result = tool_input.first_number - tool_input.second_number
            else:
                raise ValueError(f"Unsupported operation: {operation}. Use 'add' or 'subtract'")
            
            print(f"Result: {result}")
            
            # Format response using output schema
            response = CalculationToolOutput(
                result=result,
                error=None
            )
            
            return response.json()
            
        except Exception as e:
            print(f"Error in CalculationTool: {str(e)}")
            return CalculationToolOutput(
                result=0.0,
                error=str(e)
            ).json()

# def main():
#     tool = CalculationTool()
#     # Test addition
#     result = tool._run(
#         first_number=10.5,
#         second_number=5.5,
#         operation="add"
#     )
#     print("Addition test:", result)
    
#     # Test subtraction
#     result = tool._run(
#         first_number=10.5,
#         second_number=5.5,
#         operation="subtract"
#     )
#     print("Subtraction test:", result)

# if __name__ == "__main__":
#     main()