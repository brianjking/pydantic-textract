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
from llama_index.program import MultiModalLLMCompletionProgram
from llama_index.multi_modal_llms import OpenAIMultiModal

# Authentication function using environment variables for secrets
def check_password():
    """Checks if the entered password matches the one stored in environment variables."""
    def password_entered():
        # Use .get for st.session_state to avoid KeyError and provide a default empty string
        entered_password = st.session_state.get("password", "")
        # Use os.environ.get with a default empty string to avoid NoneType if the environment variable is missing
        stored_password = os.environ.get("password", "")  # Ensure this matches the actual environment variable key
        # Securely compare the entered password against the stored password
        if hmac.compare_digest(entered_password, stored_password):
            st.session_state["password_correct"] = True
            # Optionally clear the password from session state for security, if not needed elsewhere
            # del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Display the password input field
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    # Check the password correctness flag and display an error if incorrect
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    # Return the status of password correctness
    return st.session_state.get("password_correct", False)

# Stop execution if the password check fails
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

# Initialize the multi-modal model
openai_mm_llm = OpenAIMultiModal(
    model="gpt-4-vision-preview",
    api_key=os.environ.get("OPENAI_API_KEY"),
    max_new_tokens=1000
)

# Schema selection
SCHEMA_SELECTION = {
    "CFM Processing": CFM,
    "Cocktail Menus": Menu,
}

# Prompt templates for each schema
PROMPT_TEMPLATES = {
    "CFM Processing": """\
    Please convert the following image of a text document into structured data: \
    Here is the text: {text} \
    """,
    "Cocktail Menus": """\
    Please extract the menu items from the following image and text of a cocktail menu. \
    For each cocktail, provide its name, main ingredients, price, and any other relevant details. \
    Here is the text: {text} \
    """
}

# Function for basic text extraction with Textract
def process_image_with_textract(image_bytes):
    try:
        response = textract_client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        return response
    except Exception as e:
        st.error(f"Error processing document with Textract: {e}")
        return None

# Function to extract text from Textract response
def extract_text_from_textract(textract_response):
    text = ""
    for item in textract_response.get('Blocks', []):
        if item["BlockType"] == "LINE":
            text += item.get("Text", "") + "\n"
    return text.strip()

# Streamlit UI code
st.title('Document OCR and Schema Mapping')

# File uploader and schema selection
uploaded_file = st.file_uploader("Upload a document image", type=["jpg", "png", "pdf"])
selected_schema_name = st.selectbox("Select the schema for data extraction:", options=list(SCHEMA_SELECTION.keys()))
selected_schema = SCHEMA_SELECTION[selected_schema_name]

if uploaded_file is not None:
    # Read the image file
    image_bytes = uploaded_file.read()
    # Display the image
    st.image(image_bytes, caption='Uploaded Image', use_column_width=True)
    # Perform OCR with Textract
    textract_response = process_image_with_textract(image_bytes)
    # Extract text from Textract response
    extracted_text = extract_text_from_textract(textract_response)

    # Determine image mimetype (assuming JPEG as default)
    image_mimetype = "image/jpeg"
    if uploaded_file.type == "png":
        image_mimetype = "image/png"
    
    # Prepare the data for the multi-modal LLM
    prompt_template_str = PROMPT_TEMPLATES[selected_schema_name].format(text=extracted_text)
    image_document = {"image": {"data": image_bytes, "image_mimetype": image_mimetype}, "text": extracted_text}  # Pass image and text
    openai_program = MultiModalLLMCompletionProgram.from_defaults(
        output_parser=PydanticOutputParser(output_cls=selected_schema),
        image_documents=[image_document], 
        prompt_template_str=prompt_template_str,
        multi_modal_llm=openai_mm_llm,
        verbose=True,
    )
    # Execute the program and get the result
    result = openai_program()

    # Display the result in the Streamlit app
    if result:
        st.success("Data mapped to Pydantic schema successfully!")
        st.json(result.dict())
    else:
        st.error("Failed to generate structured data.")
