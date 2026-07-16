from loguru import logger


class AdherenceMonitor:
    def __init__(self):
        pass

    def check_missed_doses(self) -> None:
        logger.debug("Checking for missed doses")
        pass

    def generate_adherence_report(self, patient_id: str) -> dict:
        logger.info(f"Generating adherence report for patient {patient_id}")
        return {"patient_id": patient_id, "adherence_rate": 0.0}
