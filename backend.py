import re
import PyPDF2
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, File, UploadFile, Form
import uvicorn

# Firebase setup
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()

# -------- Helper: Parse Answer Paper --------
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

# -------- API Endpoints --------

# Step 1: Create Course + Exam Set
@app.post("/create_exam_set")
async def create_exam_set(course_name: str = Form(...), exam_set_name: str = Form(...)):
    course_id = course_name.lower().replace(" ", "_")
    exam_set_id = exam_set_name.lower().replace(" ", "_")

    # Create course doc if not exists
    db.collection("courses").document(course_id).set({
        "course_name": course_name
    }, merge=True)

    # Create exam set doc
    db.collection("courses").document(course_id).collection("exam_sets").document(exam_set_id).set({
        "exam_set_name": exam_set_name
    }, merge=True)

    return {"message": f"✅ Exam set '{exam_set_name}' created in course '{course_name}'"}

# Step 2: Upload Marks Scheme (JSON or CSV parsing can be added later)
@app.post("/upload_marks_scheme")
async def upload_marks_scheme(course_name: str = Form(...), exam_set_name: str = Form(...), file: UploadFile = File(...)):
    course_id = course_name.lower().replace(" ", "_")
    exam_set_id = exam_set_name.lower().replace(" ", "_")

    # For now assume file is TXT/JSON with lines like "Q1|5|Differentiate sep and end"
    content = (await file.read()).decode("utf-8")
    marks_scheme = {}
    for line in content.splitlines():
        parts = line.split("|")
        if len(parts) == 3:
            q, max_marks, scheme = parts
            marks_scheme[q.strip()] = {"max_marks": int(max_marks.strip()), "scheme": scheme.strip()}

    db.collection("courses").document(course_id).collection("exam_sets").document(exam_set_id).set({
        "marks_scheme": marks_scheme
    }, merge=True)

    return {"message": f"✅ Marks scheme uploaded for {exam_set_name}"}

# Step 3: Upload Student Answer Sheet
@app.post("/upload_answer")
async def upload_answer(course_name: str = Form(...), exam_set_name: str = Form(...), file: UploadFile = File(...)):
    course_id = course_name.lower().replace(" ", "_")
    exam_set_id = exam_set_name.lower().replace(" ", "_")

    # Extract PDF text
    reader = PyPDF2.PdfReader(file.file)
    text_data = ""
    for page in reader.pages:
        text_data += page.extract_text() + "\n"

    parsed_data = parse_answer_paper(text_data)
    student_id = parsed_data["student_name"].replace(" ", "_").lower()

    db.collection("courses").document(course_id).collection("exam_sets").document(exam_set_id).collection("answer_sheets").document(student_id).set(parsed_data)

    return {"message": f"✅ Uploaded answer sheet for {parsed_data['student_name']}"}

@app.get("/get_responses")
def get_responses(course_name: str, exam_set_name: str):
    course_id = course_name.lower().replace(" ", "_")
    exam_set_id = exam_set_name.lower().replace(" ", "_")

    answers_ref = db.collection("courses").document(course_id).collection("exam_sets").document(exam_set_id).collection("answer_sheets")
    docs = answers_ref.stream()

    results = []
    for doc in docs:
        results.append(doc.to_dict())

    return results


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
