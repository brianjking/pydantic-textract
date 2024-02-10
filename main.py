import os
import hmac
import io
from pydantic import BaseModel, ValidationError
import streamlit as st
import boto3
from PIL import Image
from pdf2image import convert_from_bytes
from llama_index.program import OpenAIPydanticProgram
from llama_index.output_parsers import PydanticOutputParser
from llama_index.llms import OpenAI
from schema import CFM, Menu, ActivityTypeEnum, MediaTypeEnum

# Authentication function using environment variables for secrets
def check_password():
    def password_entered():
        entered_password = st.session_state.get("password", "")
        stored_password = os.environ.get("password", "")
        if hmac.compare_digest(entered_password, stored_password):
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return st.session_state.get("password_correct", False)

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

# Schema selection
SCHEMA_SELECTION = {
    "CFM Processing": CFM,
    "Cocktail Menus": Menu,
}

# Prompt templates for each schema
PROMPT_TEMPLATES = {
    "CFM Processing": "Based on the following extracted text from a bill / invoice / receipt, carefully fill out the information fields accurately without adding any details not present in the text. If a detail is not mentioned, explicitly mark it as 'Unknown'. All fields must be filled, if a field cannot be filled with data from the extracted text - specify it as 'Unknown'. If you do a good job, you will receive a $200 tip. Carefully work step by step and review the entire text for context, you're an expert at processing this data. Here is the text: {text}",
    "Cocktail Menus": "Please extract the menu items from the following text. For each cocktail, provide its name, main ingredients, price, and any other relevant details. Format the output as a list of cocktails, with each item containing the fields 'cocktail_name', 'brand', 'product', 'ingredients', 'price', 'size', and 'description'. An example of a 'Brand' is Jack Daniel's or 'Absolut' and an example of a Product would be 'Absolut Strawberry Vodka' or 'Absolut Vodka' or 'Jack Daniel's Whiskey'. If certain information is not available, mark it as 'Unknown'. Ensure that each 'ingredient' entry is a list of individual ingredients. Here is the text: {text}"
}

def process_image_with_textract(image_bytes):
    try:
        response = textract_client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        return response
    except Exception as e:
        st.error(f"Error processing document with Textract: {e}")
        return None

def extract_text_from_textract(textract_response):
    text = ""
    for item in textract_response.get('Blocks', []):
        if item["BlockType"] == "LINE":
            text += item.get("Text", "") + "\n"
    return text.strip()

def call_llama_index_to_process_data(extracted_text, schema_cls, schema_name):
    prompt_template_str = PROMPT_TEMPLATES[schema_name].format(text=extracted_text)
    try:
        program = OpenAIPydanticProgram.from_defaults(
            output_parser=PydanticOutputParser(output_cls=schema_cls),
            output_cls=schema_cls,
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

selected_schema_name = st.selectbox("Select the schema for data extraction:", options=list(SCHEMA_SELECTION.keys()))
selected_schema = SCHEMA_SELECTION[selected_schema_name]

uploaded_file = st.file_uploader("Upload a document image", type=["jpg", "png", "pdf"])
if uploaded_file is not None:
    image_bytes = uploaded_file.read()
    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(image_bytes)
        for image in images:
            st.image(image, use_column_width=True)
    else:
        image = Image.open(io.BytesIO(image_bytes))
        st.image(image, caption='Uploaded Image', use_column_width=True)

    textract_response = process_image_with_textract(image_bytes)
    extracted_text = extract_text_from_textract(textract_response)

    # Using an expander for the extracted text
    with st.expander("Extracted Text from Images"):
        st.text_area("Extracted Text:", extracted_text, height=150)

    if extracted_text:
        structured_data = call_llama_index_to_process_data(extracted_text, selected_schema, selected_schema_name)
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
