# course-copilot-eval
PyPDF2 → read PDF text
firebase-admin → to interact with Firebase


## schema
```
courses (collection)
  └── {course_id} (document)
       ├── course_name: string
       └── exam_sets (subcollection)
            └── {exam_set_id} (document)
                 ├── exam_set_name: string
                 ├── marks_scheme (map OR subcollection)
                 │     └── Q1: { max_marks: int, scheme: string }
                 │     └── Q2: { max_marks: int, scheme: string }
                 └── answer_sheets (subcollection)
                       └── {student_id} (document)
                            ├── student_name: string
                            ├── email: string
                            ├── submitted_at: timestamp/string
                            └── responses: [
                                  { question: string, answer: string, marks: int/null }
                              ]
```

## firestore collection
courses/{course_id}/exam_sets/{exam_set_id}
  ├── exam_set_name
  ├── marks_scheme (map or subcollection)
  └── answer_sheets/{student_id}
