# backend.py
import re
import PyPDF2
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, File, UploadFile
import uvicorn

# Firebase setup
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()

def parse_answer_paper(text):
    subject_match = re.search(r"^(.*?)\n", text)
    student_match = re.search(r"Submitted by:\s*(.*)", text)
    email_match = re.search(r"Email:\s*(.*)", text)
    date_match = re.search(r"Submitted at:\s*(.*)", text)

    subject = subject_match.group(1).strip() if subject_match else None
    student_name = student_match.group(1).strip() if student_match else None
    email = email_match.group(1).strip() if email_match else None
    submitted_at = date_match.group(1).strip() if date_match else None

    qa_pattern = re.compile(r"Question\s*\d+\.(.*?)Answer:(.*?)(?=Question\s*\d+\.|$)", re.S)
    responses = []
    for match in qa_pattern.finditer(text):
        question = match.group(1).strip()
        answer = match.group(2).strip()
        responses.append({
            "question": question,
            "answer": answer,
            "marks": None
        })

    return {
        "student_name": student_name,
        "email": email,
        "subject": subject,
        "submitted_at": submitted_at,
        "responses": responses
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Extract text
    reader = PyPDF2.PdfReader(file.file)
    text_data = ""
    for page in reader.pages:
        text_data += page.extract_text() + "\n"

    parsed_data = parse_answer_paper(text_data)

    # Use student name as doc id
    doc_id = parsed_data["student_name"].replace(" ", "_").lower()
    db.collection("answer_papers").document(doc_id).set(parsed_data)

    return {"message": "✅ Uploaded successfully", "student": parsed_data["student_name"]}
    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
