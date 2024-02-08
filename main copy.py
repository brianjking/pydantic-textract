import streamlit as st
import boto3
from PIL import Image
import io
from pydantic import ValidationError
from llama_index.program import OpenAIPydanticProgram
from llama_index.output_parsers import PydanticOutputParser
from llama_index.prompts import ChatPromptTemplate, ChatMessage
from llama_index.llms import OpenAI
from schema import InsAds  # Add this import statement

# Initialize AWS Textract client
textract_client = boto3.client(
    service_name='textract',
    region_name=st.secrets["aws_region_name"]
)

# Initialize the OpenAI client
openai_client = OpenAI(model="gpt-4-0125-preview")

def process_image_with_textract(image_bytes):
    try:
        response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
        return response
    except Exception as e:
        st.error(f"Error processing document with Textract: {e}")
        return None

def extract_text_from_textract(textract_response):
    text_lines = []
    if textract_response:
        for item in textract_response['Blocks']:
            if item["BlockType"] == "LINE":
                text_lines.append(item.get("Text", ""))
    return "\n".join(text_lines)

def call_llama_index_to_process_data(extracted_text):
    prompt_template = ChatPromptTemplate(
        message_templates=[
            ChatMessage(role="system", content="You are an AI trained to extract structured data from text."),
            ChatMessage(role="user", content=extracted_text)
        ]
    )
    prompt_template_str = prompt_template.format_messages()

    try:
        program = OpenAIPydanticProgram.from_defaults(
            output_parser=PydanticOutputParser(output_cls=InsAds),  # Your Pydantic model
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
    image = Image.open(io.BytesIO(image_bytes))
    st.image(image, caption='Uploaded Image', use_column_width=True)

    textract_response = process_image_with_textract(image_bytes)
    extracted_text = extract_text_from_textract(textract_response)

    if extracted_text:
        structured_data = call_llama_index_to_process_data([extracted_text])  # Ensure extracted_text is passed as a list
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
