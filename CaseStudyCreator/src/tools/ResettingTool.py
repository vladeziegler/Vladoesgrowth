from typing import Type, Optional
from pydantic import BaseModel, Field, PrivateAttr

# from pydantic.v1 import BaseModel, Field, PrivateAttr
from crewai_tools import BaseTool

from embedchain import App
import logging

class ResetDatabaseInput(BaseModel):
    """Input for ResetDatabase."""
    confirm: bool = Field(
        default=True,
        description="Confirmation to reset the database"
    )

class ResetDatabaseOutput(BaseModel):
    """Output for ResetDatabase."""
    success: bool = Field(..., description="Whether the reset was successful")
    message: str = Field(..., description="Status message about the reset operation")

class ResetDatabaseTool(BaseTool):
    name: str = "Reset Database"
    description: str = "Resets the vector database, clearing all stored content."
    args_schema: Type[BaseModel] = ResetDatabaseInput
    
    _app: Optional[App] = PrivateAttr(default=None)

    def __init__(self, app: App):
        super().__init__()
        self._app = app

    def _run(self, confirm: bool = True) -> str:
        try:
            if not confirm:
                return "Database reset cancelled"
            
            self._app.reset()
            logging.info("Database reset successful")
            return "Database has been successfully reset"
            
        except Exception as e:
            error_message = f"Error resetting database: {str(e)}"
            logging.error(error_message)
            return error_message