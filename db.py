"""All database access. Every statement here is hand-written SQL (sqlite3 module only)."""
import sqlite3
from pathlib import Path

import matching
from seed_data import CANDIDATES, JOBS

BASE = Path(__file__).parent
DEFAULT_DB = BASE / "recruiter.db"


def connect(path=DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript((BASE / "schema.sql").read_text(encoding="utf-8"))


def seed(conn: sqlite3.Connection) -> None:
    """Wipe and reload the seed data, so calling it twice is safe."""
    with conn:
        conn.execute("DELETE FROM candidate_skills")
        conn.execute("DELETE FROM job_skills")
        conn.execute("DELETE FROM candidates")
        conn.execute("DELETE FROM jobs")
        for name, skills, years, availability, traits, quirk in CANDIDATES:
            cur = conn.execute(
                "INSERT INTO candidates (name, experience_years, availability, traits, quirk) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, years, availability, traits, quirk))
            conn.executemany(
                "INSERT INTO candidate_skills (candidate_id, skill) VALUES (?, ?)",
                [(cur.lastrowid, s) for s in skills])
        for title, skills, min_exp, culture, tagline in JOBS:
            cur = conn.execute(
                "INSERT INTO jobs (title, min_experience, culture_keywords, tagline) VALUES (?, ?, ?, ?)",
                (title, min_exp, culture, tagline))
            conn.executemany(
                "INSERT INTO job_skills (job_id, skill) VALUES (?, ?)",
                [(cur.lastrowid, s) for s in skills])


def is_empty(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 0


def _job_skills(conn, job_id: int):
    rows = conn.execute("SELECT skill FROM job_skills WHERE job_id = ? ORDER BY skill", (job_id,)).fetchall()
    return [r["skill"] for r in rows]


def _candidate_skills(conn, candidate_id: int):
    rows = conn.execute(
        "SELECT skill FROM candidate_skills WHERE candidate_id = ? ORDER BY skill", (candidate_id,)).fetchall()
    return [r["skill"] for r in rows]


def list_candidates(conn):
    rows = conn.execute(
        "SELECT id, name, experience_years, availability, traits, quirk FROM candidates ORDER BY id").fetchall()
    result = []
    for r in rows:
        item = dict(r)
        item["skills"] = _candidate_skills(conn, r["id"])
        result.append(item)
    return result


def list_jobs(conn):
    rows = conn.execute(
        "SELECT id, title, min_experience, culture_keywords, tagline FROM jobs ORDER BY id").fetchall()
    result = []
    for r in rows:
        item = dict(r)
        item["required_skills"] = _job_skills(conn, r["id"])
        result.append(item)
    return result


def _fit_fields(matched, required, experience, min_experience):
    """Score plus the pieces the UI needs to explain it."""
    skill_pts, exp_pts = matching.breakdown(len(matched), len(required), experience, min_experience)
    return {
        "score": matching.score(len(matched), len(required), experience, min_experience),
        "skill_points": round(skill_pts, 1),
        "experience_points": round(exp_pts, 1),
        "matched_skills": matched,
        "missing_skills": [s for s in required if s not in matched],
    }


def matches_for_job(conn, job_id: int):
    """Ranked candidates for a job, or None if the job does not exist."""
    job = conn.execute(
        "SELECT id, title, min_experience, culture_keywords, tagline FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job is None:
        return None
    required = _job_skills(conn, job_id)
    # Inner joins: a candidate with zero overlapping skills is simply not a match.
    rows = conn.execute(
        "SELECT c.id, c.name, c.experience_years, c.availability, c.traits, c.quirk, "
        "       GROUP_CONCAT(js.skill, ',') AS matched_names "
        "FROM candidates c "
        "JOIN candidate_skills cs ON cs.candidate_id = c.id "
        "JOIN job_skills js ON js.skill = cs.skill AND js.job_id = ? "
        "GROUP BY c.id", (job_id,)).fetchall()
    results = []
    for r in rows:
        matched = sorted(r["matched_names"].split(","))
        item = {
            "candidate_id": r["id"],
            "name": r["name"],
            "experience_years": r["experience_years"],
            "availability": r["availability"],
            "traits": r["traits"],
            "quirk": r["quirk"],
            "reason": matching.reason(", ".join(matched), len(matched), len(required),
                                      r["experience_years"], job["min_experience"], r["availability"]),
        }
        item.update(_fit_fields(matched, required, r["experience_years"], job["min_experience"]))
        results.append(item)
    results.sort(key=matching.sort_key)
    total = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    return {
        "job": {**dict(job), "required_skills": required},
        "excluded_count": total - len(results),
        "matches": results,
        # kept for convenience / backwards compatibility
        "job_id": job["id"],
        "job_title": job["title"],
    }


def matches_for_candidate(conn, candidate_id: int):
    """Ranked jobs for a candidate, or None if the candidate does not exist."""
    cand = conn.execute(
        "SELECT id, name, experience_years, availability, traits, quirk FROM candidates WHERE id = ?",
        (candidate_id,)).fetchone()
    if cand is None:
        return None
    rows = conn.execute(
        "SELECT j.id, j.title, j.min_experience, j.culture_keywords, j.tagline, "
        "       GROUP_CONCAT(js.skill, ',') AS matched_names "
        "FROM jobs j "
        "JOIN job_skills js ON js.job_id = j.id "
        "JOIN candidate_skills cs ON cs.skill = js.skill AND cs.candidate_id = ? "
        "GROUP BY j.id", (candidate_id,)).fetchall()
    results = []
    for r in rows:
        required = _job_skills(conn, r["id"])
        matched = sorted(r["matched_names"].split(","))
        item = {
            "job_id": r["id"],
            "title": r["title"],
            "tagline": r["tagline"],
            "culture_keywords": r["culture_keywords"],
            "min_experience": r["min_experience"],
            "reason": matching.reason(", ".join(matched), len(matched), len(required),
                                      cand["experience_years"], r["min_experience"], cand["availability"]),
        }
        item.update(_fit_fields(matched, required, cand["experience_years"], r["min_experience"]))
        results.append(item)
    # Same candidate for every row, so availability/experience tie-breaks are constant; fall back to title.
    results.sort(key=lambda m: (-m["score"], m["title"]))
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    return {
        "candidate": {**dict(cand), "skills": _candidate_skills(conn, candidate_id)},
        "excluded_count": total - len(results),
        "matches": results,
        "candidate_id": cand["id"],
        "candidate_name": cand["name"],
    }
