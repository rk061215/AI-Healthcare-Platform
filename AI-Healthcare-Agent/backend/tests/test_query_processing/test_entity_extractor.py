from app.query_processing.entity_extractor import MedicalEntityExtractor


class TestMedicalEntityExtractor:
    def setup_method(self):
        self.extractor = MedicalEntityExtractor(confidence_threshold=0.3)

    def test_extract_empty(self):
        assert self.extractor.extract("") == []
        assert self.extractor.extract("   ") == []

    def test_extract_medication(self):
        results = self.extractor.extract("What is the dosage of metformin?")
        medications = [e for e in results if e.type == "medication"]
        assert any("metformin" in e.value.lower() for e in medications)

    def test_extract_dosage(self):
        results = self.extractor.extract("Take 500 mg twice daily")
        dosages = [e for e in results if e.type == "dosage"]
        assert any("500" in e.value for e in dosages)

    def test_extract_lab_value(self):
        results = self.extractor.extract("What is my HbA1c level?")
        labs = [e for e in results if e.type == "lab_value"]
        assert any("HbA1c" in e.value or "A1c" in e.value for e in labs)

    def test_extract_condition(self):
        results = self.extractor.extract("I have diabetes and hypertension")
        conditions = [e for e in results if e.type == "condition"]
        assert len(conditions) >= 2

    def test_extract_symptom(self):
        results = self.extractor.extract("I have chest pain and shortness of breath")
        symptoms = [e for e in results if e.type == "symptom"]
        types = {e.value.lower() for e in symptoms}
        assert "chest pain" in types or "chest" in types

    def test_extract_medication_info(self):
        meds = self.extractor.extract_medication("Take metformin 500 mg twice daily")
        assert len(meds) > 0
        assert any("metformin" in m.name.lower() for m in meds)

    def test_extract_lab_values(self):
        labs = self.extractor.extract_lab_values("HbA1c 7.2 mg/dL")
        assert len(labs) > 0
        assert any("HbA1c" in l.test_name or "A1c" in l.test_name for l in labs)
