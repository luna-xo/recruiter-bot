PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS candidates (
    id               INTEGER PRIMARY KEY,
    name             TEXT    NOT NULL UNIQUE,
    experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
    availability     TEXT    NOT NULL CHECK (availability IN ('Immediate', '2 weeks', 'Not looking')),
    traits           TEXT    NOT NULL,
    quirk            TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    skill        TEXT    NOT NULL,
    PRIMARY KEY (candidate_id, skill)
);

CREATE TABLE IF NOT EXISTS jobs (
    id               INTEGER PRIMARY KEY,
    title            TEXT    NOT NULL UNIQUE,
    min_experience   INTEGER NOT NULL CHECK (min_experience >= 0),
    culture_keywords TEXT    NOT NULL,
    tagline          TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    skill  TEXT    NOT NULL,
    PRIMARY KEY (job_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_candidate_skills_skill ON candidate_skills(skill);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill);
