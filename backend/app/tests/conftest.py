from __future__ import annotations
import socket
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.neo4j import neo4j_client

from sqlalchemy import text
from app.db.postgres import engine


# -----------------------------
# Helpers (timestamp + folders)
# -----------------------------
def _timestamp() -> str:
    # Example: 2026-02-21_14-30-45
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _setup_test_logger(log_file: Path) -> logging.Logger:
    """
    Dedicated test-run logger:
    - writes to a timestamped file
    - avoids duplicated handlers across imports
    """
    logger = logging.getLogger("mira.tests")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # do not duplicate into root logger

    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# -----------------------------
# pytest session/report hooks
# -----------------------------
def pytest_configure(config: pytest.Config) -> None:
    """
    Runs once at pytest startup.
    Creates:
    - backend/test_logs/test_log_<timestamp>.log
    - backend/test_reports/test_report_<timestamp>.html
    and wires pytest-html to use the timestamped report automatically.
    """
    # rootpath will be backend/ because you run pytest from backend/
    backend_root = Path(config.rootpath)

    logs_dir = backend_root / "test_logs"
    reports_dir = backend_root / "test_reports"
    _ensure_dir(logs_dir)
    _ensure_dir(reports_dir)

    stamp = _timestamp()
    log_file = logs_dir / f"test_log_{stamp}.log"
    report_file = reports_dir / f"test_report_{stamp}.html"

    config._mira_test_log_file = log_file  # type: ignore[attr-defined]
    config._mira_test_report_file = report_file  # type: ignore[attr-defined]

    # auto-set html report path if pytest-html is installed
    if hasattr(config.option, "htmlpath"):
        config.option.htmlpath = str(report_file)
        if hasattr(config.option, "self_contained_html"):
            config.option.self_contained_html = True


def pytest_sessionstart(session: pytest.Session) -> None:
    config = session.config
    log_file: Path = config._mira_test_log_file  # type: ignore[attr-defined]
    report_file: Path = config._mira_test_report_file  # type: ignore[attr-defined]

    logger = _setup_test_logger(log_file)
    config._mira_test_logger = logger  # type: ignore[attr-defined]

    logger.info("=" * 80)
    logger.info("TEST SESSION START")
    logger.info("Log file: %s", log_file)
    logger.info("HTML report: %s", report_file)
    logger.info("=" * 80)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]):
    """
    Logs PASS/FAIL for each test.
    Only logs the 'call' phase to avoid noise.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    logger: logging.Logger = item.config._mira_test_logger  # type: ignore[attr-defined]
    test_name = report.nodeid

    if report.passed:
        logger.info("PASS | %s | duration=%.4fs", test_name, report.duration)
    elif report.failed:
        logger.info("FAIL | %s | duration=%.4fs", test_name, report.duration)
        if report.longrepr:
            logger.info("ERROR DETAILS:\n%s", report.longrepr)
    elif report.skipped:
        logger.info("SKIP | %s | duration=%.4fs", test_name, report.duration)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    logger: logging.Logger = session.config._mira_test_logger  # type: ignore[attr-defined]
    logger.info("=" * 80)
    logger.info("TEST SESSION END | exitstatus=%s", exitstatus)
    logger.info("Tests collected: %s", session.testscollected)
    logger.info("Artifacts:")
    logger.info("Log file: %s", session.config._mira_test_log_file)  # type: ignore[attr-defined]
    logger.info("HTML report: %s", session.config._mira_test_report_file)  # type: ignore[attr-defined]
    logger.info("=" * 80)


# -----------------------------
# Fixtures (your originals)
# -----------------------------
@pytest.fixture(scope="session", autouse=True)
def neo4j_connection():
    """
    Connect once per test session.
    This avoids relying purely on FastAPI startup hooks.
    """
    neo4j_client.connect()
    yield
    neo4j_client.close()


@pytest.fixture()
def client():
    """
    Provide a FastAPI TestClient that runs startup/shutdown events reliably.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def created_concepts():
    """
    Tracks concept_ids created during a test.
    Test code should append concept_id into this list.
    Cleanup removes only those concepts/embeddings.
    """
    concept_ids: list[str] = []
    yield concept_ids

    # --- Neo4j cleanup: delete only created concept versions ---
    if concept_ids:
        with neo4j_client.driver.session() as session:
            session.run(
                """
                MATCH (c:Concept)
                WHERE c.concept_id IN $ids
                DETACH DELETE c
                """,
                ids=concept_ids,
            )

    # --- Postgres cleanup: delete only embeddings for those concept_ids ---
    if concept_ids:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM concept_embeddings WHERE concept_id = ANY(:ids)"),
                {"ids": concept_ids},
            )

    # --- Postgres cleanup (optional): remove only test-generated query logs ---
    # If your tests use source="test_suite" or "test_*", clean those only:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM query_logs WHERE source LIKE 'test%'"))


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def pytest_runtest_setup(item):
    if item.get_closest_marker("integration"):
        # Neo4j bolt 7687, Postgres 5433 (your config), Qdrant 6333 optional
        neo4j_ok = _port_open("localhost", 7687)
        pg_ok = _port_open("localhost", 5433)
        if not (neo4j_ok and pg_ok):
            pytest.skip("Skipping integration test: Neo4j/Postgres not reachable")