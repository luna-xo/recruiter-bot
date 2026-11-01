import unittest

import db
import matching


class ScoreTests(unittest.TestCase):
    def test_perfect_match(self):
        self.assertEqual(matching.score(3, 3, 8, 3), 100.0)

    def test_partial_skills_full_experience(self):
        self.assertEqual(matching.score(1, 2, 5, 2), 65.0)  # 0.7*0.5 + 0.3*1

    def test_under_experienced(self):
        self.assertEqual(matching.score(2, 2, 2, 4), 85.0)  # 0.7*1 + 0.3*0.5


class MatchTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        db.seed(self.conn)

    def test_detective_job_ranks_sherlock_first(self):
        job_id = self.conn.execute("SELECT id FROM jobs WHERE title = 'Backend Detective'").fetchone()[0]
        result = db.matches_for_job(self.conn, job_id)
        self.assertEqual(result["matches"][0]["name"], "Sherlock H.")
        self.assertEqual(result["matches"][0]["score"], 100.0)

    def test_candidate_with_no_overlap_is_excluded(self):
        job_id = self.conn.execute("SELECT id FROM jobs WHERE title = 'Backend Detective'").fetchone()[0]
        names = [m["name"] for m in db.matches_for_job(self.conn, job_id)["matches"]]
        self.assertNotIn("Ron S.", names)

    def test_reverse_direction(self):
        cand_id = self.conn.execute("SELECT id FROM candidates WHERE name = 'Rick S.'").fetchone()[0]
        result = db.matches_for_candidate(self.conn, cand_id)
        self.assertEqual(result["matches"][0]["title"], "Rapid Prototyping Engineer")

    def test_unknown_ids(self):
        self.assertIsNone(db.matches_for_job(self.conn, 999))
        self.assertIsNone(db.matches_for_candidate(self.conn, 999))

    def test_seed_is_idempotent(self):
        db.seed(self.conn)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 15)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 6)


if __name__ == "__main__":
    unittest.main()
