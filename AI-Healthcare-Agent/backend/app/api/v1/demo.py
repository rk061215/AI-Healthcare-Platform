import time
import uuid
from typing import Any

from fastapi import APIRouter, UploadFile, File, Form

router = APIRouter(prefix="/demo", tags=["Demo"])

DEMO_SESSION: dict[str, Any] = {}

PREDEFINED_SCENARIOS = [
    {
        "id": "cardiology",
        "title": "Cardiology Report",
        "description": "A comprehensive cardiac evaluation with echocardiogram and stress test results",
        "file_type": "pdf",
        "extracted_data": {
            "patient_name": "John Doe",
            "age": 58,
            "gender": "Male",
            "report_type": "Cardiology Consultation",
            "findings": [
                "Mild left ventricular hypertrophy",
                "Normal sinus rhythm at 72 bpm",
                "Ejection fraction: 55%",
                "No significant valvular abnormalities",
            ],
            "measurements": {
                "blood_pressure": "138/88 mmHg",
                "heart_rate": "72 bpm",
                "cholesterol_ldl": "142 mg/dL",
                "cholesterol_hdl": "48 mg/dL",
                "triglycerides": "165 mg/dL",
            },
            "diagnosis": "Stage 1 Hypertension with mild LVH",
            "recommendations": [
                "Initiate ACE inhibitor therapy",
                "Low sodium diet",
                "Follow-up in 3 months",
            ],
        },
        "ocr_confidence": 0.94,
    },
    {
        "id": "lab_work",
        "title": "Complete Blood Count & Metabolic Panel",
        "description": "Routine laboratory workup with CBC and comprehensive metabolic panel",
        "file_type": "png",
        "extracted_data": {
            "patient_name": "Jane Smith",
            "age": 34,
            "gender": "Female",
            "report_type": "Laboratory Report",
            "findings": [
                "WBC: 6.2 x10^9/L (normal)",
                "Hemoglobin: 13.8 g/dL (normal)",
                "Platelets: 245 x10^9/L (normal)",
                "Glucose: 98 mg/dL (normal)",
                "Creatinine: 0.9 mg/dL (normal)",
                "ALT: 28 U/L (normal)",
            ],
            "measurements": {
                "wbc": "6.2 x10^9/L",
                "hemoglobin": "13.8 g/dL",
                "hematocrit": "41%",
                "platelets": "245 x10^9/L",
                "glucose": "98 mg/dL",
                "creatinine": "0.9 mg/dL",
                "bun": "14 mg/dL",
                "alt": "28 U/L",
                "ast": "24 U/L",
            },
            "diagnosis": "All results within normal limits",
            "recommendations": ["No follow-up necessary", "Routine annual screening"],
        },
        "ocr_confidence": 0.97,
    },
    {
        "id": "radiology",
        "title": "Chest X-Ray Report",
        "description": "Radiological examination of chest for respiratory symptoms",
        "file_type": "jpg",
        "extracted_data": {
            "patient_name": "Robert Johnson",
            "age": 45,
            "gender": "Male",
            "report_type": "Radiology Report",
            "findings": [
                "Clear lung fields bilaterally",
                "No consolidation or effusion",
                "Cardiac silhouette within normal limits",
                "No acute osseous abnormalities",
            ],
            "measurements": {
                "cardiothoracic_ratio": "0.48",
                "lung_volumes": "Adequate",
            },
            "diagnosis": "Normal chest radiograph",
            "recommendations": ["No further imaging required"],
        },
        "ocr_confidence": 0.91,
    },
]


@router.post("/upload")
async def demo_upload(file: UploadFile = File(...)):
    report_id = str(uuid.uuid4())
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "pdf"

    import random

    scenario = random.choice(PREDEFINED_SCENARIOS)
    data = scenario["extracted_data"]
    confidence = scenario["ocr_confidence"]

    DEMO_SESSION[report_id] = {
        "id": report_id,
        "title": file.filename or data["report_type"],
        "file_type": ext,
        "extracted_data": data,
        "ocr_confidence": confidence,
        "created_at": time.time(),
    }

    return {
        "id": report_id,
        "title": file.filename or data["report_type"],
        "file_type": ext,
        "extracted_data": data,
        "ocr_confidence": confidence,
        "suggestions": [
            "Review extracted data for accuracy",
            "Ask questions about specific findings",
            "Export the report for your records",
        ],
    }


@router.post("/ask")
async def demo_ask(
    question: str = Form(...),
    report_id: str = Form(None),
    report_text: str = Form(None),
    conversation_history: str = Form("[]"),
):
    import json
    import random

    start = time.time()

    history = json.loads(conversation_history) if conversation_history else []

    q_lower = question.lower()

    if "blood" in q_lower or "pressure" in q_lower:
        answer = "Based on the report, the patient's blood pressure is 138/88 mmHg, which falls in the Stage 1 Hypertension range according to the ACC/AHA guidelines. The report notes mild left ventricular hypertrophy, which can be associated with chronic hypertension."
        citations = [
            {
                "source": "Report Findings",
                "snippet": "Blood Pressure: 138/88 mmHg",
                "confidence": 0.98,
            },
            {
                "source": "Diagnosis Section",
                "snippet": "Stage 1 Hypertension with mild LVH",
                "confidence": 0.95,
            },
        ]
    elif "cholesterol" in q_lower or "lipid" in q_lower:
        answer = "The lipid panel shows: LDL cholesterol at 142 mg/dL (borderline high), HDL at 48 mg/dL (normal), and triglycerides at 165 mg/dL (borderline high). The LDL level suggests the patient may benefit from dietary modifications and potentially statin therapy, especially given the history of hypertension."
        citations = [
            {
                "source": "Lipid Panel",
                "snippet": "LDL: 142 mg/dL, HDL: 48 mg/dL, Triglycerides: 165 mg/dL",
                "confidence": 0.97,
            },
            {
                "source": "Recommendations",
                "snippet": "Initiate ACE inhibitor therapy, Low sodium diet",
                "confidence": 0.92,
            },
        ]
    elif "diagnosis" in q_lower or "what" in q_lower or "result" in q_lower:
        answer = "The report diagnoses Stage 1 Hypertension with mild left ventricular hypertrophy (LVH). Key findings include elevated blood pressure at 138/88 mmHg, normal sinus rhythm, preserved ejection fraction at 55%, and no significant valvular abnormalities. The recommended treatment plan includes ACE inhibitor therapy and lifestyle modifications."
        citations = [
            {
                "source": "Diagnosis",
                "snippet": "Stage 1 Hypertension with mild LVH",
                "confidence": 0.96,
            },
            {
                "source": "Echocardiogram",
                "snippet": "Ejection fraction: 55%, Mild left ventricular hypertrophy",
                "confidence": 0.94,
            },
        ]
    elif "medication" in q_lower or "drug" in q_lower or "treat" in q_lower:
        answer = "The report recommends initiating ACE inhibitor therapy for hypertension management. ACE inhibitors are first-line treatment for Stage 1 hypertension, particularly when there is evidence of target organ damage such as LVH. The patient should also implement lifestyle modifications including a low-sodium diet and regular exercise."
        citations = [
            {
                "source": "Treatment Plan",
                "snippet": "Initiate ACE inhibitor therapy",
                "confidence": 0.93,
            },
            {
                "source": "Clinical Guidelines",
                "snippet": "ACC/AHA Hypertension Guidelines recommend ACEi for Stage 1 HTN with LVH",
                "confidence": 0.88,
            },
        ]
    elif "follow" in q_lower or "next" in q_lower or "appointment" in q_lower:
        answer = "The report recommends a follow-up appointment in 3 months to assess response to ACE inhibitor therapy and monitor blood pressure. Additional recommendations include a low-sodium diet and routine annual screening for lipid profile and renal function."
        citations = [
            {
                "source": "Recommendations",
                "snippet": "Follow-up in 3 months",
                "confidence": 0.95,
            },
            {
                "source": "Lifestyle",
                "snippet": "Low sodium diet",
                "confidence": 0.90,
            },
        ]
    else:
        answer = f"Regarding your question about '{question}': Based on the medical report analysis, the patient presents with Stage 1 Hypertension and mild LVH. The overall clinical picture suggests a good prognosis with appropriate medical management. Key vital signs and lab values are within manageable ranges. Would you like to know more about specific medications, dietary recommendations, or follow-up scheduling?"
        citations = [
            {
                "source": "Report Summary",
                "snippet": "Stage 1 Hypertension with mild left ventricular hypertrophy. Ejection fraction: 55%",
                "confidence": 0.91,
            },
            {
                "source": "Vitals",
                "snippet": "Blood Pressure: 138/88 mmHg, Heart Rate: 72 bpm",
                "confidence": 0.93,
            },
        ]

    elapsed = int((time.time() - start) * 1000)

    suggested_questions = [
        "What are the key findings in this report?",
        "What medications are recommended?",
        "When should the patient follow up?",
        "Are there any abnormal lab values?",
    ]

    confidence_level = "high" if random.random() > 0.3 else "medium"

    return {
        "answer": answer,
        "citations": citations,
        "confidence": {
            "overall": round(random.uniform(0.85, 0.98), 2),
            "level": confidence_level,
        },
        "suggested_questions": suggested_questions,
        "processing_time_ms": elapsed,
    }


@router.get("/scenarios")
async def demo_scenarios():
    return PREDEFINED_SCENARIOS


@router.post("/reset")
async def demo_reset():
    DEMO_SESSION.clear()
    return {"message": "Demo session reset successfully"}
