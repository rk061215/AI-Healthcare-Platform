import re
from typing import Optional


def sanitize_text(text: str, max_length: int = 10000) -> str:
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return cleaned[:max_length]


def validate_email(email: str) -> Optional[str]:
    email = email.strip().lower()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    return None


def validate_phone(phone: str) -> Optional[str]:
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    if re.match(r'^\+?\d{7,15}$', cleaned):
        return cleaned
    return None


def sanitize_filename(filename: str) -> str:
    filename = filename.replace('\\', '/').split('/')[-1]
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    filename = re.sub(r'[^\w\.\-\(\) ]', '_', filename)
    if len(filename) > 255:
        name, ext = re.match(r'^(.+?)(\.[^.]*)?$', filename).groups()
        if ext:
            filename = name[:255-len(ext)] + ext
        else:
            filename = filename[:255]
    return filename


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, 'Password must be at least 8 characters'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain an uppercase letter'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain a lowercase letter'
    if not re.search(r'[0-9]', password):
        return False, 'Password must contain a digit'
    return True, 'Password is valid'
