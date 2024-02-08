import os
from pydantic import BaseModel, ValidationError, validator
from enum import Enum
import streamlit as st
import boto3
from PIL import Image
import io
import hmac
from pdf2image import convert_from_bytes  # Ensure this library is installed for handling PDFs
from llama_index.program import OpenAIPydanticProgram
from llama_index.output_parsers import PydanticOutputParser
from llama_index.llms import OpenAI
#from schema import InsAds, ActivityTypeEnum, MediaTypeEnum  #Imports schema for CFM invoices.
from MenuItem import MenuItem, ActivityTypeEnum, MediaTypeEnum # Imports Menu Item Schema


# Authentication function using environment variables for secrets
def check_password():
    """Returns `True` if the user had the correct password using environment variables."""
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], os.environ.get("password")):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

# AWS Textract client configuration
textract_client = boto3.client(
    service_name='textract',
    region_name=os.environ.get("aws_region_name"),
    aws_access_key_id=os.environ.get("aws_access_key_id"),
    aws_secret_access_key=os.environ.get("aws_secret_access_key")
)

# OpenAI client initialization
openai_client = OpenAI(
    model="gpt-4-0125-preview",
    api_key=os.environ.get("openai_api_key")
)

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
    prompt_template_str = f"""\
    Based on the following extracted text from a bill / invoice / receipt, carefully fill out the information fields accurately without adding any details not present in the text. If a detail is not mentioned, explicitly mark it as 'Unknown'. All fields must be filled, if a field cannot be filled with data from the extracted text - specify it as 'Unknown'. If you do a good job, you will receive a $200 tip. Carefully work step by step and review the entire text for context, you're an expert at processing this data. Here is the text: {extracted_text}
    """
    try:
        program = OpenAIPydanticProgram.from_defaults(
            output_parser=PydanticOutputParser(output_cls=MenuItems),
            output_cls=InsAds,
            prompt_template_str=prompt_template_str,
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
    # Handle PDF files
    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(image_bytes)
        for image in images:
            st.image(image, use_column_width=True)
    else:
        image = Image.open(io.BytesIO(image_bytes))
        st.image(image, caption='Uploaded Image', use_column_width=True)

    textract_response = process_image_with_textract(image_bytes)
    extracted_text = extract_text_from_textract(textract_response)

    st.subheader("Extracted Text:")
    st.text(extracted_text)

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
