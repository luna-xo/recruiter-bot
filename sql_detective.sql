-- Answers for Part 2. Load sql_detective_data.sql first (SQLite / Postgres compatible).

-- Question 1: all open job postings with their recruiter's name
SELECT jp.id, jp.title, jp.department, r.name AS recruiter
FROM job_postings jp
JOIN recruiters r ON r.id = jp.recruiter_id
WHERE jp.status = 'open'
ORDER BY jp.id;

-- Question 2: applicants who reached the Final stage, per job posting
-- (reached = has a Final interview row, whatever its outcome; LEFT JOIN keeps postings with 0)
SELECT jp.id, jp.title,
       COUNT(DISTINCT i.applicant_id) AS final_stage_applicants
FROM job_postings jp
LEFT JOIN interviews i ON i.job_posting_id = jp.id AND i.stage = 'Final'
GROUP BY jp.id, jp.title
ORDER BY jp.id;

-- Question 3: people who effectively applied to more than one job posting
-- Dirty data: Ananya Rao is two applicant rows (ids 1 and 2) whose emails differ only by case,
-- so a person is identified by LOWER(email). An applicant is tied to a posting through interviews.
SELECT MIN(a.full_name) AS person,
       LOWER(a.email) AS email,
       COUNT(DISTINCT i.job_posting_id) AS postings
FROM applicants a
JOIN interviews i ON i.applicant_id = a.id
GROUP BY LOWER(a.email)
HAVING COUNT(DISTINCT i.job_posting_id) > 1
ORDER BY person;

-- Question 4: Final-stage conversion rate per recruiter (at least 3 Final-stage interviews)
SELECT r.id, r.name,
       COUNT(*) AS final_interviews,
       SUM(CASE WHEN i.outcome = 'passed' THEN 1 ELSE 0 END) AS passed,
       ROUND(1.0 * SUM(CASE WHEN i.outcome = 'passed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS conversion_rate
FROM interviews i
JOIN job_postings jp ON jp.id = i.job_posting_id
JOIN recruiters r ON r.id = jp.recruiter_id
WHERE i.stage = 'Final'
GROUP BY r.id, r.name
HAVING COUNT(*) >= 3
ORDER BY r.id;

-- Question 5 (Bonus): recruiter with the most Final-stage passes per department (window function)
-- RANK keeps ties; departments with no placements are left out.
SELECT department, recruiter, placements
FROM (
    SELECT jp.department,
           r.name AS recruiter,
           COUNT(*) AS placements,
           RANK() OVER (PARTITION BY jp.department ORDER BY COUNT(*) DESC) AS rnk
    FROM interviews i
    JOIN job_postings jp ON jp.id = i.job_posting_id
    JOIN recruiters r ON r.id = jp.recruiter_id
    WHERE i.stage = 'Final' AND i.outcome = 'passed'
    GROUP BY jp.department, r.id, r.name
) ranked
WHERE rnk = 1
ORDER BY department;
