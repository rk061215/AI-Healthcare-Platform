import re

PATIENT_NAME_PATTERN = re.compile(r"\b([A-Z][a-z]+)\s([A-Z][a-z]+)\b")
EMAIL_PATTERN = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
PHONE_PATTERN = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
DOB_PATTERN = re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b")
MRN_PATTERN = re.compile(r"\b(MRN|mrn)[:\s]*(\d{6,10})\b")
JWT_PATTERN = re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")
API_KEY_PATTERN = re.compile(r"(sk-[a-zA-Z0-9-]{10,}|lsv2_[a-zA-Z0-9]{40,})")

MASK_REPLACEMENTS: dict[str, str] = {
    "patient_name": "[PATIENT NAME]",
    "email": "[EMAIL]",
    "phone": "[PHONE]",
    "ssn": "[SSN]",
    "dob": "[DOB]",
    "mrn": "[MRN]",
    "jwt": "[JWT]",
    "api_key": "[API KEY]",
}


def mask_pii(text: str) -> str:
    text = SSN_PATTERN.sub(MASK_REPLACEMENTS["ssn"], text)
    text = EMAIL_PATTERN.sub(MASK_REPLACEMENTS["email"], text)
    text = MRN_PATTERN.sub(lambda m: f"{m.group(1)}: {MASK_REPLACEMENTS['mrn']}", text)
    text = JWT_PATTERN.sub(MASK_REPLACEMENTS["jwt"], text)
    text = API_KEY_PATTERN.sub(MASK_REPLACEMENTS["api_key"], text)
    text = DOB_PATTERN.sub(MASK_REPLACEMENTS["dob"], text)
    text = PHONE_PATTERN.sub(MASK_REPLACEMENTS["phone"], text)
    return text


def mask_pii_in_dict(data: dict, depth: int = 0) -> dict:
    if depth > 5:
        return data
    result: dict = {}
    for key, value in data.items():
        if isinstance(value, str):
            if key.lower() in {"patient_id", "request_id", "user_id", "doctor_id"}:
                result[key] = value
            else:
                result[key] = mask_pii(value)
        elif isinstance(value, dict):
            result[key] = mask_pii_in_dict(value, depth + 1)
        elif isinstance(value, list):
            result[key] = [
                mask_pii_in_dict(item, depth + 1) if isinstance(item, dict) else (
                    mask_pii(item) if isinstance(item, str) else item
                )
                for item in value
            ]
        else:
            result[key] = value
    return result


def mask_pii_in_log_message(message: str) -> str:
    if not message:
        return message
    return mask_pii(message)
