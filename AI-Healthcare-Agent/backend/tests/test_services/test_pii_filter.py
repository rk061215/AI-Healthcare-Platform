from app.core.pii_filter import mask_pii, mask_pii_in_dict, mask_pii_in_log_message


def test_mask_ssn():
    result = mask_pii("My SSN is 123-45-6789")
    assert "[SSN]" in result
    assert "123-45-6789" not in result


def test_mask_email():
    result = mask_pii("Contact: john.doe@example.com")
    assert "[EMAIL]" in result
    assert "john.doe@example.com" not in result


def test_mask_phone():
    result = mask_pii("Call me at (555) 123-4567")
    assert "[PHONE]" in result
    assert "(555) 123-4567" not in result


def test_mask_jwt():
    result = mask_pii("Token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNqP")
    assert "[JWT]" in result
    assert "eyJhbGciOiJIUzI1NiJ9" not in result


def test_mask_api_key():
    result = mask_pii("Key: sk-proj-abc123def456ghi789jkl012")
    assert "[API KEY]" in result
    assert "sk-proj" not in result


def test_mask_dob():
    result = mask_pii("Born on 01/15/1990")
    assert "[DOB]" in result
    assert "01/15/1990" not in result


def test_mask_mrn():
    result = mask_pii("MRN: 1234567890")
    assert "[MRN]" in result
    assert "1234567890" not in result


def test_mask_pii_in_dict():
    data = {
        "patient_id": "pat_123",
        "notes": "John Smith called about SSN 123-45-6789",
        "nested": {
            "contact": "john@test.com",
        },
    }
    result = mask_pii_in_dict(data)
    assert result["patient_id"] == "pat_123"
    assert "[SSN]" in result["notes"]
    assert "123-45-6789" not in result["notes"]
    assert "[EMAIL]" in result["nested"]["contact"]
    assert "john@test.com" not in result["nested"]["contact"]


def test_mask_pii_in_log_message_empty():
    assert mask_pii_in_log_message("") == ""
    assert mask_pii_in_log_message(None) is None


def test_mask_pii_in_dict_preserves_keys():
    data = {
        "request_id": "req_abc123",
        "user_id": "usr_456",
        "patient_id": "pat_789",
        "doctor_id": "doc_012",
    }
    result = mask_pii_in_dict(data)
    assert result["request_id"] == "req_abc123"
    assert result["user_id"] == "usr_456"
    assert result["patient_id"] == "pat_789"
    assert result["doctor_id"] == "doc_012"
