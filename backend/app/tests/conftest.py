from __future__ import annotations

import logging
import os
import platform
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import bindparam, text

from app.db.postgres import engine
from app.main import app

# -----------------------------
# Helpers (timestamp + folders)
# -----------------------------
def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _setup_test_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("mira.tests")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _neo4j_host_port() -> tuple[str, int]:
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    u = urlparse(uri)
    host = u.hostname or "localhost"
    port = u.port or 7687
    return host, port


def _postgres_host_port() -> tuple[str, int]:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5433"))
    return host, port


def _neo4j_enabled() -> bool:
    """
    Neo4j should only be considered enabled if we have all required env vars.
    This prevents Settings() validation issues in minimal runs.
    """
    return bool(os.getenv("NEO4J_URI") and os.getenv("NEO4J_USER") and os.getenv("NEO4J_PASSWORD"))


def _get_neo4j_client():
    """
    Lazy import to avoid triggering Settings() validation unless Neo4j is enabled.
    """
    from app.db.neo4j import neo4j_client  # local import on purpose
    return neo4j_client


# -----------------------------
# pytest session/report hooks
# -----------------------------
def pytest_configure(config: pytest.Config) -> None:
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
    config._mira_test_start = datetime.now()  # type: ignore[attr-defined]

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
    logger.info("Python: %s", sys.version.replace("\n", " "))
    logger.info("Platform: %s | %s", platform.platform(), platform.machine())
    logger.info("Pytest: %s", pytest.__version__)
    logger.info("CWD: %s", os.getcwd())
    logger.info("Neo4j enabled: %s", _neo4j_enabled())
    logger.info("=" * 80)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]):
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


def pytest_warning_recorded(
    warning_message: Any,
    when: str,
    nodeid: str,
    location: tuple[str, int, str] | None,
) -> None:
    msg = str(warning_message)
    record = f"{when} | {nodeid} | {msg}"
    pytest._mira_warning_buffer = getattr(pytest, "_mira_warning_buffer", [])  # type: ignore[attr-defined]
    pytest._mira_warning_buffer.append(record)  # type: ignore[attr-defined]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    logger: logging.Logger = session.config._mira_test_logger  # type: ignore[attr-defined]
    start: datetime = session.config._mira_test_start  # type: ignore[attr-defined]
    duration = (datetime.now() - start).total_seconds()
    warnings = getattr(pytest, "_mira_warning_buffer", [])  # type: ignore[attr-defined]

    logger.info("=" * 80)
    logger.info("TEST SESSION END | exitstatus=%s", exitstatus)
    logger.info("Tests collected: %s", session.testscollected)
    logger.info("Total duration: %.2fs", duration)

    if warnings:
        logger.info("Warnings: %d", len(warnings))
        for w in warnings[:20]:
            logger.info("WARNING | %s", w)
        if len(warnings) > 20:
            logger.info("WARNING | ... (%d more warnings omitted)", len(warnings) - 20)
    else:
        logger.info("Warnings: 0")

    logger.info("Artifacts:")
    logger.info("Log file: %s", session.config._mira_test_log_file)  # type: ignore[attr-defined]
    logger.info("HTML report: %s", session.config._mira_test_report_file)  # type: ignore[attr-defined]
    logger.info("=" * 80)


# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture(scope="session", autouse=True)
def neo4j_connection():
    """
    Only connect to Neo4j if Neo4j is enabled (env vars present).
    Minimal CI run should NOT require Neo4j.
    """
    if not _neo4j_enabled():
        yield
        return

    neo4j_client = _get_neo4j_client()
    neo4j_client.connect()
    yield
    neo4j_client.close()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def created_concepts():
    """
    Tracks created concept_ids and cleans them safely.
    Neo4j cleanup runs only if Neo4j is enabled.
    Postgres cleanup always runs (safe).
    """
    concept_ids: list[str] = []
    yield concept_ids

    ids = list(dict.fromkeys(concept_ids))
    if not ids:
        return

    # --- Neo4j cleanup (only when enabled) ---
    if _neo4j_enabled():
        neo4j_client = _get_neo4j_client()
        try:
            driver = neo4j_client.driver
        except Exception:
            driver = None

        if driver is not None:
            with driver.session() as session:
                session.run(
                    """
                    MATCH (c:Concept)
                    WHERE c.concept_id IN $ids
                    DETACH DELETE c
                    """,
                    ids=ids,
                )

    # --- Postgres cleanup: embeddings for those ids ---
    stmt = text("DELETE FROM concept_embeddings WHERE concept_id IN :ids").bindparams(
        bindparam("ids", expanding=True)
    )
    with engine.begin() as conn:
        conn.execute(stmt, {"ids": ids})

    # --- Postgres cleanup: test-generated query logs ---
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM query_logs WHERE source LIKE 'test%'"))


# -----------------------------
# Integration gating (skip if deps down)
# -----------------------------
def pytest_runtest_setup(item: pytest.Item) -> None:
    if item.get_closest_marker("integration"):
        neo_host, neo_port = _neo4j_host_port()
        pg_host, pg_port = _postgres_host_port()

        neo4j_ok = _port_open(neo_host, neo_port)
        pg_ok = _port_open(pg_host, pg_port)

        if not (neo4j_ok and pg_ok):
            pytest.skip(
                f"Skipping integration test: deps not reachable "
                f"(neo4j={neo_host}:{neo_port} pg={pg_host}:{pg_port})"
            )
