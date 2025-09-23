import re
import PyPDF2
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def extract_text_from_pdf(file_path):
    text_data = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text_data += page.extract_text() + "\n"
    return text_data

def parse_answer_paper(text):
    # Extract metadata
    subject_match = re.search(r"^(.*?)\n", text)
    student_match = re.search(r"Submitted by:\s*(.*)", text)
    email_match = re.search(r"Email:\s*(.*)", text)
    date_match = re.search(r"Submitted at:\s*(.*)", text)

    subject = subject_match.group(1).strip() if subject_match else None
    student_name = student_match.group(1).strip() if student_match else None
    email = email_match.group(1).strip() if email_match else None
    submitted_at = date_match.group(1).strip() if date_match else None

    # Split into Q&A
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

def store_in_firebase(doc_id, data):
    db.collection("answer_papers").document(doc_id).set(data)
    print(f"✅ Stored paper for {data['student_name']}")

if __name__ == "__main__":
    pdf_path = "sample.pdf"
    raw_text = extract_text_from_pdf(pdf_path)
    parsed_data = parse_answer_paper(raw_text)
    store_in_firebase("aishwarya_m_001", parsed_data)
