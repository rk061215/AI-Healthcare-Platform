from __future__ import annotations

import json
import re
import time as time_module
from typing import Optional

from app.ai.base_provider import BaseProvider
from app.core.prompt_loader import PromptLoader
from app.medical_parser.exceptions import (
    AIExtractorError,
    EmptyOCRError,
    InvalidAIContentError,
    RegexExtractorError,
    RetryExhaustedError,
)
from app.medical_parser.schemas import (
    ExtractionContext,
    LabResultExtracted,
    MedicalReportSchema,
    MedicationExtracted,
)
from app.medical_parser.types import SourceType


class AIExtractor:
    """Extract structured medical data using an AI provider via BaseProvider.

    Never calculates confidence.
    Never normalizes values.
    Returns only a validated MedicalReportSchema.
    """

    def __init__(
        self,
        provider: BaseProvider,
        prompt_path: str = "medical/report_analysis",
        max_retries: int = 3,
        retry_delay_seconds: float = 2.0,
    ):
        self._provider = provider
        self._prompt_path = prompt_path
        self._max_retries = max_retries
        self._retry_delay = retry_delay_seconds

    def extract(self, ocr_text: str, context: ExtractionContext) -> MedicalReportSchema:
        if not ocr_text or not ocr_text.strip():
            raise EmptyOCRError("OCR text is empty or whitespace-only")

        prompt = PromptLoader.load(self._prompt_path)
        rendered = prompt.render(text=ocr_text)
        system_prompt = self._build_system_prompt(prompt.metadata)
        output_schema = MedicalReportSchema.model_json_schema()

        last_error: Optional[str] = None

        for attempt in range(self._max_retries):
            try:
                raw = self._provider.generate_structured_output(
                    prompt=rendered,
                    output_schema=output_schema,
                    system_prompt=system_prompt,
                )

                context.raw_ai_response = json.dumps(raw, indent=2) if isinstance(raw, dict) else str(raw)

                if not isinstance(raw, dict):
                    raise InvalidAIContentError(f"AI returned non-dict: {type(raw).__name__}")

                schema = MedicalReportSchema(**raw)
                context.source = SourceType.AI
                return schema

            except InvalidAIContentError:
                raise

            except Exception as e:
                last_error = str(e)
                if attempt < self._max_retries - 1:
                    time_module.sleep(self._retry_delay * (2 ** attempt))

        raise RetryExhaustedError(
            f"AI extraction failed after {self._max_retries} attempts: {last_error}"
        )

    def _build_system_prompt(self, metadata: dict) -> str:
        parts: list[str] = []
        guardrails = metadata.get("guardrails", [])
        if isinstance(guardrails, list):
            parts.append("Rules:")
            for g in guardrails:
                parts.append(f"- {g}")
        parts.append("")
        parts.append("Return ONLY a valid JSON object. No markdown fences. No explanatory text.")
        return "\n".join(parts)


class RegexExtractor:
    """Fallback extraction using improved regex patterns.

    Never calculates confidence.
    Never normalizes values.
    Returns only a validated MedicalReportSchema.
    """

    PROMPT_PATH = "medical/report_analysis"

    def extract(self, ocr_text: str, context: ExtractionContext) -> MedicalReportSchema:
        if not ocr_text or not ocr_text.strip():
            raise EmptyOCRError("OCR text is empty or whitespace-only")

        lines = ocr_text.split("\n")
        text_lower = ocr_text.lower()

        schema = MedicalReportSchema(
            patient_name=self._extract_field(lines, r"(?:Patient\s*Name\s*[:.]?\s*)(.+?)(?:\s{2,}|$)"),
            date_of_birth=self._extract_field(lines, r"(?:DOB|Date\s*of\s*Birth|Birth\s*Date)\s*[:.]?\s*([\d\-/\.\s]+)"),
            document_date=self._extract_field(lines, r"(?:Date|Date\s*of\s*Service)\s*[:.]?\s*([\d\-/\.\s]+)"),
            doctor_name=self._extract_field(lines, r"(?:Dr\.|Doctor|Physician)\s*[:.]?\s*(.+?)(?:\s{2,}|$)"),
            hospital_name=self._extract_hospital_name(lines, original_text=ocr_text),
            diagnosis=self._extract_field(lines, r"(?:Diagnosis|Dx|Impression)\s*[:.]?\s*(.+?)(?:\s{2,}|$)"),
            medications=self._extract_medications(lines, text_lower, ocr_text),
            lab_results=self._extract_lab_results(lines, text_lower),
            follow_up_date=self._extract_field(lines, r"(?:Follow[-\s]*up|Review)\s*[:.]?\s*([\d\-/\.\s]+)"),
            doctor_instructions=self._extract_notes(lines, text_lower),
            notes="",
        )

        context.source = SourceType.REGEX
        return schema

    @staticmethod
    def _extract_field(lines: list[str], pattern: str) -> str:
        for line in lines:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if val:
                    return val
        return ""

    @staticmethod
    def _extract_medications(
        lines: list[str], text_lower: str, original_text: str
    ) -> list[MedicationExtracted]:
        meds: list[MedicationExtracted] = []
        in_meds = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r"^(?:Medications?|Meds|Rx|Prescriptions?)\s*[:.]?\s*$", stripped, re.IGNORECASE):
                in_meds = True
                continue

            if in_meds:
                if re.match(r"^(?:Lab|Diagnosis|Notes|Follow-up|--+|__+)", stripped, re.IGNORECASE):
                    in_meds = False
                    continue

                med_match = re.match(
                    r"([A-Za-z\s]+)\s+(\d+\.?\d*\s*(?:mg|mcg|g|ml|IU|units?))\s*(.*)",
                    stripped,
                    re.IGNORECASE,
                )
                if med_match:
                    meds.append(MedicationExtracted(
                        name=med_match.group(1).strip(),
                        dosage=med_match.group(2).strip(),
                        instructions=med_match.group(3).strip() or "",
                    ))

        if not meds:
            rx_match = re.findall(
                r"([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\s+(\d+\.?\d*\s*(?:mg|mcg|g|ml|IU))",
                original_text,
                re.IGNORECASE,
            )
            for name, dosage in rx_match:
                meds.append(MedicationExtracted(
                    name=name.strip(),
                    dosage=dosage.strip(),
                ))

        return meds

    @staticmethod
    def _extract_lab_results(lines: list[str], text_lower: str) -> list[LabResultExtracted]:
        results: list[LabResultExtracted] = []
        in_labs = False

        for line in lines:
            stripped = line.strip()
            if re.match(r"^(?:Lab\s*Results?|Laboratory)\s*[:.]?\s*$", stripped, re.IGNORECASE):
                in_labs = True
                continue

            if in_labs:
                if re.match(r"^(?:Medications?|Diagnosis|Notes|Follow-up|--+|__+)", stripped, re.IGNORECASE):
                    in_labs = False
                    continue

                lab_match = re.match(
                    r"([A-Za-z\s/]+)\s*[:]?\s*([\d\.\/]+)\s*([A-Za-z/%]+)",
                    stripped,
                )
                if lab_match:
                    results.append(LabResultExtracted(
                        test_name=lab_match.group(1).strip(),
                        value=lab_match.group(2).strip(),
                        unit=lab_match.group(3).strip(),
                    ))

        return results

    @staticmethod
    def _extract_notes(lines: list[str], text_lower: str) -> str:
        notes: list[str] = []
        in_notes = False
        for line in lines:
            stripped = line.strip()
            m = re.match(r"^(?:Notes|Comments|Remarks|Instructions)\s*[:.]?\s*(.*)$", stripped, re.IGNORECASE)
            if m:
                inline = m.group(1).strip()
                if inline:
                    notes.append(inline)
                else:
                    in_notes = True
                continue
            if in_notes:
                if re.match(r"^(?:--+|__+|Follow-up|Rx:)", stripped, re.IGNORECASE):
                    break
                notes.append(stripped)
        return " ".join(notes)

    @staticmethod
    def _extract_hospital_name(lines: list[str], original_text: str) -> str:
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            m = re.match(r"(?:Hospital|Clinic|Medical\s*Center)\s*[:.]?\s*(.+)", stripped, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if val and not re.match(r"^[ :.]+$", val):
                    return val

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(
                r"^(?!.*(?:Dr\.|Doctor|Patient|Date|DOB|Diagnosis|Medications?|Lab|Follow-up|Notes))"
                r".*\b(?:Hospital|Clinic|Medical\s*Center)\b.*$",
                stripped, re.IGNORECASE,
            ):
                return stripped

        return ""


def extract(
    ocr_text: str,
    provider: BaseProvider,
    prompt_path: str = "medical/report_analysis",
    max_retries: int = 3,
    retry_delay_seconds: float = 2.0,
) -> tuple[MedicalReportSchema, ExtractionContext]:
    """Primary extraction entry point.

    Tries AI extraction first, falls back to regex on failure.
    Returns (schema, context) where context carries source tracking metadata.
    """
    context = ExtractionContext()

    try:
        ai_extractor = AIExtractor(
            provider=provider,
            prompt_path=prompt_path,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )
        schema = ai_extractor.extract(ocr_text, context)
        return schema, context

    except Exception as ai_error:
        context.validation_errors.append(f"AI extraction failed: {ai_error}")

        try:
            regex_extractor = RegexExtractor()
            schema = regex_extractor.extract(ocr_text, context)
            return schema, context

        except Exception as regex_error:
            raise RegexExtractorError(
                f"AI extraction failed ({ai_error}) and regex fallback failed ({regex_error})"
            ) from ai_error
