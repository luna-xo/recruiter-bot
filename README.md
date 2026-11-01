# Recruiter Bot

A small backend that stores candidates and jobs and ranks matches in both directions.
Python 3 standard library only (`http.server` + `sqlite3`), all SQL hand-written. No ORM, no installs.

## Run

```
python app.py            # open http://localhost:8000 for a small viewer page; creates recruiter.db and seeds it on first start
python test_bot.py       # tests
```

## API

```
curl localhost:8000/candidates
curl localhost:8000/jobs
curl localhost:8000/jobs/1/matches          # ranked candidates for a job
curl localhost:8000/candidates/6/matches    # ranked jobs for a candidate
curl -X POST localhost:8000/seed            # wipe and reload the seed data
```

Each match has a `score` (0-100) and a short `reason`. Unknown ids return 404.

## Schema (`schema.sql`)

`candidates`, `jobs`, and two join tables `candidate_skills` / `job_skills` (one row per skill, so
overlap is a plain SQL join). A match is not stored: it is computed on request, so it can never go stale.

## Matching algorithm

`score = 100 * (0.7 * skill_fit + 0.3 * experience_fit)`

- **skill_fit** = matched required skills / total required skills. Skills are the core of fit, so 70%.
- **experience_fit** = 1 if the candidate meets the minimum, else experience / minimum. Exceeding the
  minimum earns nothing extra, so a 20-year veteran does not outrank a perfect-skill 8-year candidate.
- Candidates with **zero** skill overlap are left out rather than listed with a low score.
- **Tie-break:** earlier availability (Immediate, 2 weeks, Not looking), then more experience, then name.
- Availability is shown in the reason but does not change the score: "Not looking" people are still
  relevant matches, a recruiter just needs to see that.
- Traits and culture keywords are stored but not scored. The seed data uses different vocabularies for
  them (e.g. "blunt" vs "autonomous"), so any scoring would be guesswork.

Trade-off: the SQL finds overlapping skills and counts them; the weighting is applied in Python
(`matching.py`) so it is easy to read and test.

## Part 2

`sql_detective_data.sql` loads the dataset as given; `sql_detective.sql` has the five answers.
Q3 treats applicants 1 and 2 (Ananya Rao, emails differing only by case) as one person.

## AI usage

Built with Claude Code. I reviewed the design and queries and ran the tests and SQL answers.
