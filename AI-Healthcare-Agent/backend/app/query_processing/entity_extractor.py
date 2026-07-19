from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.query_processing.exceptions import EntityExtractionError


class MedicationInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None


class DosageInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str
    unit: str
    substance: Optional[str] = None


class LabValueInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    test_name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    is_abnormal: bool = False


class ExtractedEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str
    value: str
    confidence: float = 1.0
    start_pos: int = 0
    end_pos: int = 0
    normalized: Optional[str] = None
    metadata: dict = {}


MEDICATION_PATTERNS = [
    re.compile(r"(?i)\b([A-Z][a-z]+(?:x|cin|mycin|mide|pam|lam|pine|zole|caine|pril|sartan|vastatin|dipine|lukast|navir|vir|cycline|cillin|zole|pram|tidine|prazole|oxacin|conazole|afil|parin|mab|cept|nib|ib))"),
    re.compile(r"(?i)\b(aspirin|ibuprofen|acetaminophen|paracetamol|metformin|omeprazole|atorvastatin|lisinopril|amlodipine|levothyroxine)\b"),
]

DOSAGE_PATTERNS = [
    re.compile(r"(?i)(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|iu|units|tablet|capsule|cap|tab|pill|patch|puff|drop|spray|injection)"),
    re.compile(r"(?i)(\d+(?:\.\d+)?)\s*%\s*(?:cream|ointment|gel|solution|suspension)"),
]

FREQUENCY_PATTERNS = [
    re.compile(r"(?i)(\d+)\s*(?:times?\s*(?:a|per|each|every)\s*(?:day|daily|week|month)|x\s*(?:/|per)\s*(?:day|d|week|wk))"),
    re.compile(r"(?i)\b(qd|bid|tid|qid|prn|q\d+h|qhs|qam|qpm|ac|pc|hs|stat|ss)\b"),
]

ROUTE_PATTERNS = [
    re.compile(r"(?i)\b(po|oral|by\s*mouth|iv|intravenous|im|intramuscular|sc|subcutaneous|sl|sublingual|topical|inhaled|pr|per\s*rectum|od|os|ou|otic|ophthalmic|intranasal|transdermal)\b"),
]

LAB_PATTERNS = [
    re.compile(r"(?i)\b(?:blood\s*)?(glucose|HbA1c|A1c|hemoglobin|cholesterol|HDL|LDL|triglycerides|creatinine|BUN|sodium|potassium|chloride|calcium|WBC|RBC|platelet|hematocrit|MCV|MCH|MCHC|RDW|INR|PT|PTT|TSH|T4|T3|ALT|AST|ALP|GGT|bilirubin|albumin|protein|cortisol|vitamin\s*D|ferritin|iron|B12|folate)"),
    re.compile(r"(?i)(\d+(?:\.\d+)?)\s*(mg/dL|mmol/L|ng/mL|pg/mL|mEq/L|U/L|IU/L|fL|pg|g/dL|%|cells/mcL|k/uL|m/uL)"),
]

CONDITION_PATTERNS = [
    re.compile(r"(?i)\b(diabetes|hypertension|hyperlipidemia|asthma|COPD|CHF|CAD|PVD|CKD|ESRD|HIV|AIDS|hepatitis|cirrhosis|pancreatitis|IBD|Crohn's|colitis|RA|OA|SLE|lupus|MS|Parkinson's|Alzheimer's|dementia|depression|anxiety|bipolar|schizophrenia|thyroid|hypothyroid|hyperthyroid)\b"),
    re.compile(r"(?i)\b(cancer|tumor|carcinoma|sarcoma|melanoma|leukemia|lymphoma|neoplasm|malignancy|metastasis)\b"),
]

SYMPTOM_PATTERNS = [
    re.compile(r"(?i)\b(pain|ache|sore|tender|swelling|inflammation|redness|warmth|numbness|tingling|burning|stiffness|fatigue|weakness|dizziness|lightheaded|nausea|vomiting|diarrhea|constipation|fever|chills|sweat|cough|shortness\s*of\s*breath|SOB|dyspnea|chest\s*pain|palpitations|headache|blurred\s*vison|vision\s*changes|weight\s*(loss|gain|lost|gained)|loss\s*of\s*appetite|anorexia|insomnia|fatigue|malaise|lethargy)\b"),
]

ANATOMY_PATTERNS = [
    re.compile(r"(?i)\b(heart|lung|liver|kidney|brain|spine|bone|joint|muscle|nerve|artery|vein|skin|stomach|intestine|colon|rectum|bladder|uterus|ovary|prostate|breast|thyroid|lymph\s*node|blood\s*vessel)\b"),
]


class MedicalEntityExtractor:
    def __init__(self, confidence_threshold: float = 0.4):
        self._threshold = confidence_threshold

    def extract(self, query: str) -> list[ExtractedEntity]:
        if not query or not query.strip():
            return []

        entities: list[ExtractedEntity] = []
        seen: set[str] = set()

        try:
            entities.extend(self._extract_type(query, "medication", MEDICATION_PATTERNS, seen))
            entities.extend(self._extract_type(query, "dosage", DOSAGE_PATTERNS, seen))
            entities.extend(self._extract_type(query, "frequency", FREQUENCY_PATTERNS, seen))
            entities.extend(self._extract_type(query, "route", ROUTE_PATTERNS, seen))
            entities.extend(self._extract_type(query, "lab_value", LAB_PATTERNS, seen))
            entities.extend(self._extract_type(query, "condition", CONDITION_PATTERNS, seen))
            entities.extend(self._extract_type(query, "symptom", SYMPTOM_PATTERNS, seen))
            entities.extend(self._extract_type(query, "anatomy", ANATOMY_PATTERNS, seen))
        except Exception as exc:
            raise EntityExtractionError(f"Entity extraction failed: {exc}") from exc

        return entities

    def _extract_type(
        self, query: str, entity_type: str, patterns: list[re.Pattern], seen: set[str]
    ) -> list[ExtractedEntity]:
        results: list[ExtractedEntity] = []
        for pattern in patterns:
            for match in pattern.finditer(query):
                value = match.group(0).strip()
                dedup_key = f"{entity_type}:{value.lower()}"
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    results.append(ExtractedEntity(
                        type=entity_type,
                        value=value,
                        confidence=0.5 if entity_type in ("dosage", "lab_value") else 0.6,
                        start_pos=match.start(),
                        end_pos=match.end(),
                    ))
        return results

    def extract_medication(self, query: str) -> list[MedicationInfo]:
        meds: list[MedicationInfo] = []
        for match in MEDICATION_PATTERNS[0].finditer(query):
            meds.append(MedicationInfo(name=match.group(1)))
        for match in MEDICATION_PATTERNS[1].finditer(query):
            name = match.group(0).capitalize()
            if not any(m.name.lower() == name.lower() for m in meds):
                meds.append(MedicationInfo(name=name))

        dosage_map: dict[str, str] = {}
        for dm in DOSAGE_PATTERNS[0].finditer(query):
            key = f"{dm.group(1)}{dm.group(2)}".lower()
            dosage_map[key] = f"{dm.group(1)} {dm.group(2)}"

        freq_map: dict[str, str] = {}
        for fm in FREQUENCY_PATTERNS[0].finditer(query):
            freq_map[fm.group(0).lower()] = fm.group(0)
        for fm in FREQUENCY_PATTERNS[1].finditer(query):
            freq_map[fm.group(0).lower()] = fm.group(0)

        route_map: dict[str, str] = {}
        for rm in ROUTE_PATTERNS[0].finditer(query):
            route_map[rm.group(0).lower()] = rm.group(0)

        for med in meds:
            if dosage_map:
                med.dosage = next(iter(dosage_map.values()))
            if freq_map:
                med.frequency = next(iter(freq_map.values()))
            if route_map:
                med.route = next(iter(route_map.values()))

        return meds

    def extract_lab_values(self, query: str) -> list[LabValueInfo]:
        labs: list[LabValueInfo] = []
        for match in LAB_PATTERNS[0].finditer(query):
            labs.append(LabValueInfo(
                test_name=match.group(1).strip(),
                is_abnormal=self._check_abnormal_context(query, match.start(), match.end()),
            ))
        for match in LAB_PATTERNS[1].finditer(query):
            for lab in labs:
                lab.value = match.group(1)
                lab.unit = match.group(2)
        return labs

    def _check_abnormal_context(self, query: str, start: int, end: int) -> bool:
        context_before = query[max(0, start - 40):start].lower()
        context_after = query[end:min(len(query), end + 40)].lower()
        abnormal_indicators = [
            "high", "low", "abnormal", "elevated", "decreased", "increased",
            "above", "below", "out of range", "critical",
        ]
        for indicator in abnormal_indicators:
            if indicator in context_before or indicator in context_after:
                return True
        return False
