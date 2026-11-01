"""Pure scoring logic (no database, no HTTP) so it is easy to test."""

SKILL_WEIGHT = 0.7
EXPERIENCE_WEIGHT = 0.3


AVAILABILITY_RANK = {"Immediate": 0, "2 weeks": 1, "Not looking": 2}


def breakdown(matched_skills: int, required_skills: int, experience: int, min_experience: int):
    """Points earned for skills (max 70) and experience (max 30), unrounded.

    skill_fit      = matched / required                      (0..1)
    experience_fit = 1 if experience >= minimum, otherwise experience / minimum
    """
    skill_fit = matched_skills / required_skills if required_skills else 0.0
    if min_experience <= 0 or experience >= min_experience:
        experience_fit = 1.0
    else:
        experience_fit = experience / min_experience
    return 100 * SKILL_WEIGHT * skill_fit, 100 * EXPERIENCE_WEIGHT * experience_fit


def score(matched_skills: int, required_skills: int, experience: int, min_experience: int) -> float:
    """Total score from 0 to 100."""
    skill_pts, exp_pts = breakdown(matched_skills, required_skills, experience, min_experience)
    return round(skill_pts + exp_pts, 1)


def reason(matched_names: str, matched_skills: int, required_skills: int,
           experience: int, min_experience: int, availability: str) -> str:
    if experience >= min_experience:
        exp_text = f"{experience} yrs meets the {min_experience} yr minimum"
    else:
        exp_text = f"{experience} yrs is {min_experience - experience} short of the {min_experience} yr minimum"
    return (f"Matches {matched_skills}/{required_skills} required skills ({matched_names}); "
            f"{exp_text}; availability: {availability}")


def sort_key(item: dict):
    """Highest score first; ties go to earlier availability, then more experience, then name."""
    return (-item["score"], AVAILABILITY_RANK[item["availability"]], -item["experience_years"], item["name"])
