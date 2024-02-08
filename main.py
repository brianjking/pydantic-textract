import os
from pydantic import BaseModel, ValidationError, validator
from enum import Enum
import streamlit as st
import boto3
from PIL import Image
import io
import hmac
from llama_index.program import OpenAIPydanticProgram
from llama_index.output_parsers import PydanticOutputParser
from llama_index.llms import OpenAI



# Authentication function updated to use environment variables for secrets
def check_password():
    """Returns `True` if the user had the correct password using environment variables."""
    def password_entered():
        # Fetch the password from an environment variable
        if hmac.compare_digest(st.session_state["password"],
                               os.environ.get("password")):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

# Check password before proceeding
if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Existing code below...
class ActivityTypeEnum(str, Enum):
    DirectMail = "DirectMail"
    LocalAd = "LocalAd"
    # Define other activity types...

class MediaTypeEnum(str, Enum):
    Print = "Print"
    Outdoor = "Outdoor"
    # Define other media types...

class InsAds(BaseModel):
    """Data model for a CFM."""
    vendor_merchant_name: str
    bill_invoice_amount: str
    date_of_invoice: str
    media_type: MediaTypeEnum
    activity_type: ActivityTypeEnum
    comments: str
    description: str
    account_id_number: str
    invoice: str

    @classmethod
    def validate_enum(cls, v, field):
        if field.name == 'media_type':
            enum_type = MediaTypeEnum
        elif field.name == 'activity_type':
            enum_type = ActivityTypeEnum
        else:
            return v
        try:
            return enum_type(v)
        except ValueError:
            raise ValueError(f"Value {v} is not a valid {enum_type}")

    @validator('*')
    def validate_enums(cls, v, field):
        return cls.validate_enum(v, field)

# AWS Textract client configuration using environment variables

textract_client = boto3.client(
    service_name='textract',
    region_name=os.environ.get("aws_region_name"),
    aws_access_key_id=os.environ.get("aws_access_key_id"),
    aws_secret_access_key=os.environ.get("aws_secret_access_key")
)

    # Updated OpenAI client initialization using the environment variable for the API key
openai_client = OpenAI(
    model="gpt-4-0125-preview",
    api_key=os.environ.get("openai_api_key")
)

#openai_client = OpenAI(model="gpt-4-0125-preview")

def process_image_with_textract(image_bytes):
    try:
        response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
        return response
    except Exception as e:
        st.error(f"Error processing document with Textract: {e}")
        return None

def extract_text_from_textract(textract_response):
    text = ""
    if textract_response:
        for item in textract_response['Blocks']:
            if item["BlockType"] == "LINE":
                text += item.get("Text", "") + "\n"
    return text.strip()

def call_llama_index_to_process_data(extracted_text):
    try:
        program = OpenAIPydanticProgram.from_defaults(
            output_parser=PydanticOutputParser(output_cls=InsAds),
            output_cls=InsAds,
            prompt_template_str=extracted_text,  # Directly pass the extracted text
            llm=openai_client,
            verbose=True,
        )
        result = program()

        return result
    except Exception as e:
        st.error(f"Error generating schema with LlamaIndex: {e}")
        return None

st.title('Document OCR and Schema Mapping')

uploaded_file = st.file_uploader("Upload a document image", type=["jpg", "png", "pdf"])
if uploaded_file is not None:
    image_bytes = uploaded_file.read()
    image = Image.open(io.BytesIO(image_bytes))
    st.image(image, caption='Uploaded Image', use_column_width=True)

    textract_response = process_image_with_textract(image_bytes)
    extracted_text = extract_text_from_textract(textract_response)

    st.subheader("Extracted Text:")
    st.text(extracted_text)  # Display the extracted text directly onto the page

    if extracted_text:
        structured_data = call_llama_index_to_process_data(extracted_text)
        if structured_data:
            try:
                st.success("Data mapped to Pydantic schema successfully!")
                st.json(structured_data.dict())
            except ValidationError as e:
                st.error(f"Validation error in mapping data to schema: {e}")
        else:
            st.error("Failed to generate structured data.")
    else:
        st.error("No text extracted from the document.")
