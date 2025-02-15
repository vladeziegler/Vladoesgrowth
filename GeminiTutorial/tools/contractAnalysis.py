import os
import google.generativeai as genai
import PyPDF2
from pydantic import BaseModel, Field
import json
import os
import dotenv

dotenv.load_dotenv()

# Set up API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Define the complete path to your PDF file
pdf_path = "/Users/vladimirdeziegler/text_crewai/Vladoesgrowth/GeminiTutorial/PDF/Lease Agreement.pdf"

# Pydantic Models
class Landlord(BaseModel):
    first_name: str = Field(description="The first name of the landlord")
    address: str = Field(description="The address of the landlord")

class Tenant(BaseModel):
    first_name: str = Field(description="The first name of the tenant")
    address: str = Field(description="The address of the tenant")

class LeaseAgreement(BaseModel):
    landlord: Landlord = Field(description="The landlord's information")
    tenants: list[Tenant] = Field(description="List of tenants")
    deposit: str = Field(description="The deposit amount")
    rent: str = Field(description="The rent amount")
    iban: str = Field(description="The IBAN number")

def analyze_lease_document(pdf_path: str) -> str:
    """
    Analyzes a lease agreement PDF and returns the raw analysis.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Raw analysis of the lease agreement
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found at path: {pdf_path}")
        
    try:
        # Extract text from PDF
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()

        if not text:
            raise ValueError("No text extracted from the PDF.")

        # Initialize the model and analyze
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"Analyze the following lease agreement:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        raise Exception(f"Error processing PDF: {e}")

def extract_lease_agreement_json(pdf_path: str) -> LeaseAgreement:
    """
    Extracts structured data from a lease agreement PDF and returns a LeaseAgreement object.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        LeaseAgreement: Structured lease agreement data
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found at path: {pdf_path}")
        
    try:
        # Extract text from PDF
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()

        if not text:
            raise ValueError("No text extracted from the PDF.")

        # Initialize the model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Define the prompt for structured extraction
        prompt = f"""From the following lease agreement, extract both the landlord and tenant information.
        Return the result in a JSON format that matches the following schema:
        {LeaseAgreement.schema_json()}
        
        LEASE AGREEMENT TEXT:
        {text}"""

        # Generate content
        response = model.generate_content(prompt)
        
        # Clean and parse JSON
        json_string = response.text.strip()
        json_string = json_string[json_string.find('{'):json_string.rfind('}')+1]
        json_string = json_string.replace('\\\\', '\\').replace('\\"', '"')
        
        # Parse and validate
        lease_data = json.loads(json_string)
        return LeaseAgreement(**lease_data)

    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON response: {e}")
    except Exception as e:
        raise Exception(f"Error processing PDF: {e}")

# Example usage:
if __name__ == "__main__":
    pdf_path = "./GeminiTutorial/PDF/LeaseTutorial.pdf"
    
    try:
        # Get general analysis
        analysis = analyze_lease_document(pdf_path)
        print("Analysis:", analysis)
        
        # Get structured data
        lease_agreement = extract_lease_agreement_json(pdf_path)
        print("\nStructured Data:")
        print(f"Landlord: {lease_agreement.landlord.first_name}")
        for tenant in lease_agreement.tenants:
            print(f"Tenant: {tenant.first_name} ")
        print(json.dumps(lease_agreement.model_dump(), indent=4))
            
    except Exception as e:
        print(f"Error: {e}")
