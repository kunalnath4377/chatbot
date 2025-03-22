from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
import json
import PyPDF2
from docx import Document
import pytesseract
from PIL import Image
import io
import re

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Function to interact with OpenRouter API
def get_openrouter_response(prompt):
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5173",  # Optional
                "X-Title": "File Summary Chatbot",  # Optional
            },
            data=json.dumps({
                "model": "deepseek/deepseek-r1:free",  # Use the DeepSeek model on OpenRouter
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            })
        )
        print("OpenRouter API Response:", response.json())  # Debug the response
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise HTTPException(status_code=500, detail="OpenRouter API error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Function to format key points as a clean numbered list
def format_key_points(text):
    # Remove unwanted symbols like **
    text = re.sub(r"\*\*", "", text)
    
    # Split the text into lines and filter out empty lines
    points = [line.strip() for line in text.split("\n") if line.strip()]
    
    # Limit to 15 key points
    points = points[:15]
    
    # Format as a clean numbered list with two lines of gap
    formatted_points = "\n\n".join([f"{i + 1}. {point}" for i, point in enumerate(points)])
    
    return formatted_points

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from DOC/DOCX
def extract_text_from_docx(file):
    doc = Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

# Function to extract text from image using OCR
def extract_text_from_image(file):
    try:
        image = Image.open(io.BytesIO(file.read()))
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# Endpoint for file upload and summary
@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Determine the file type and extract text
        if file.content_type == "application/pdf":
            text = extract_text_from_pdf(file.file)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = extract_text_from_docx(file.file)
        elif file.content_type == "text/plain":
            text = file.file.read().decode("utf-8")
        elif file.content_type.startswith("image/"):
            text = extract_text_from_image(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Create a prompt for OpenRouter to summarize the text
        prompt = f"Summarize the following text and extract key points in a clean numbered list (maximum 15 points): {text}"
        summary = get_openrouter_response(prompt)
        
        # Format the summary as a clean numbered list
        formatted_summary = format_key_points(summary)
        return JSONResponse(content={"summary": formatted_summary})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)