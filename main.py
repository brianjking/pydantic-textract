import os
import hmac
import io
import traceback
from pydantic import BaseModel, ValidationError
import boto3
from PIL import Image
from pdf2image import convert_from_bytes
from llama_index.program.openai import OpenAIPydanticProgram
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from schema import CFM, Menu, ActivityTypeEnum, MediaTypeEnum
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = FastAPI()
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

# AWS Textract client configuration
textract_client = boto3.client(
    service_name='textract',
    region_name=os.environ.get("aws_region_name",
                               os.getenv("aws_region_name")),
    aws_access_key_id=os.environ.get("aws_access_key_id",
                                     os.getenv("aws_access_key_id")),
    aws_secret_access_key=os.environ.get("aws_secret_access_key",
                                         os.getenv("aws_secret_access_key")))

# OpenAI client initialization
Settings.llm = OpenAI(model="gpt-4-0125-preview",
                      api_key=os.environ.get("openai_api",
                                             os.getenv("openai_api")))

# Schema selection
SCHEMA_SELECTION = {
    "CFM Processing": CFM,
    "Cocktail Menus": Menu,
}

# Prompt templates for each schema
PROMPT_TEMPLATES = {
    "CFM Processing":
    "Based on the following extracted text from a bill / invoice / receipt, carefully fill out the information fields accurately without adding any details not present in the text. If a detail is not mentioned, explicitly mark it as 'Unknown'. All fields must be filled, if a field cannot be filled with data from the extracted text - specify it as 'Unknown'. If you do a good job, you will receive a $200 tip. Carefully work step by step and review the entire text for context, you're an expert at processing this data. Here is the text: {text}",
    "Cocktail Menus":
    "Please extract the menu items from the following text. For each cocktail, provide its name, main ingredients, price, and any other relevant details. Format the output as a list of cocktails, with each item containing the fields 'cocktail_name', 'brand', 'product', 'ingredients', 'price', 'size', and 'description'. An example of a 'Brand' is Jack Daniel's or 'Absolut' and an example of a Product would be 'Absolut Strawberry Vodka' or 'Absolut Vodka' or 'Jack Daniel's Whiskey'. If certain information is not available, mark it as 'Unknown'. Ensure that each 'ingredient' entry is a list of individual ingredients. Here is the text: {text}"
}


def authenticate(api_key: str = Security(api_key_header)):
    correct_password = os.environ.get("password", os.getenv("password"))
    if not api_key or not hmac.compare_digest(api_key, correct_password):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


def process_image_with_textract(image_bytes):
    try:
        response = textract_client.detect_document_text(
            Document={'Bytes': image_bytes})
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document with Textract: {str(e)}")


def extract_text_from_textract(textract_response):
    text = ""
    for item in textract_response.get('Blocks', []):
        if item["BlockType"] == "LINE":
            text += item.get("Text", "") + "\n"
    return text.strip()


def call_llama_index_to_process_data(extracted_text, schema_cls, schema_name):
    prompt_template_str = PROMPT_TEMPLATES[schema_name]
    try:
        print(f"Extracted Text: {extracted_text}")
        print(f"Prompt Template: {prompt_template_str}")
        program = OpenAIPydanticProgram.from_defaults(
            output_parser=PydanticOutputParser(output_cls=schema_cls),
            output_cls=schema_cls,
            prompt_template_str=prompt_template_str,
            verbose=True,
        )
        result = program(text=extracted_text)
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating schema with LlamaIndex: {str(e)}\nTraceback: {error_details}")


@app.post("/process_document/{schema_name}")
async def process_document(schema_name: str,
                           file: UploadFile = File(...),
                           authenticated: bool = Depends(authenticate)):
    if schema_name not in SCHEMA_SELECTION:
        raise HTTPException(status_code=400,
                            detail=f"Invalid schema name: {schema_name}")

    selected_schema = SCHEMA_SELECTION[schema_name]

    image_bytes = await file.read()
    if file.content_type == "application/pdf":
        images = convert_from_bytes(image_bytes)
        extracted_texts = []  # Hold extracted text from each page
        for image in images:
            bytes_io = io.BytesIO()
            image.save(bytes_io, format='JPEG')
            response = process_image_with_textract(bytes_io.getvalue())
            extracted_texts.append(extract_text_from_textract(response))
        extracted_text = "\n".join(
            extracted_texts)  # Combine text from all pages
    else:
        textract_response = process_image_with_textract(image_bytes)
        extracted_text = extract_text_from_textract(textract_response)

    if not extracted_text:
        raise HTTPException(status_code=400,
                            detail="No text extracted from the document.")

    structured_data = call_llama_index_to_process_data(extracted_text,
                                                       selected_schema,
                                                       schema_name)
    if not structured_data:
        raise HTTPException(status_code=500,
                            detail="Failed to generate structured data.")

    try:
        return structured_data.dict()
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error in mapping data to schema: {str(e)}")
