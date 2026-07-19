from loguru import logger

_TRACE_STEPS: list[str] = []


def probe(msg: str) -> None:
    _TRACE_STEPS.append(msg)
    logger.info(f"TRACE: {msg}")


def clear() -> None:
    _TRACE_STEPS.clear()


def get_steps() -> list[str]:
    return list(_TRACE_STEPS)


def get_count() -> int:
    return len(_TRACE_STEPS)
