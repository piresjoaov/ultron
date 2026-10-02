"""Canvas tools for retrieving the user's course grades."""
import html
import re
from datetime import datetime, timedelta

import httpx

from config import CANVAS_API_TOKEN, CANVAS_API_URL, REQUEST_TIMEOUT


def get_grades(course_prefix: str = "FA26") -> str:
    """Return weighted progress and A projections for matching Canvas courses."""
    if not CANVAS_API_TOKEN:
        return "Error: CANVAS_API_TOKEN is not configured."
    if not course_prefix or not course_prefix.strip():
        return "Error: 'course_prefix' cannot be empty."

    prefix = course_prefix.strip().upper()
    base_url = CANVAS_API_URL.rstrip("/")
    courses_url = f"{base_url}/users/self/courses"
    enrollments_url = f"{base_url}/users/self/enrollments"
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}

    try:
        with httpx.Client(headers=headers, timeout=REQUEST_TIMEOUT) as client:
            courses_response = client.get(
                courses_url,
                params={"enrollment_state": "active", "per_page": 100},
            )
            _raise_canvas_error(courses_response, "courses")
            courses = courses_response.json()

            enrollments_response = client.get(
                enrollments_url,
                params={
                    "per_page": 100,
                    "state[]": ["active", "completed"],
                },
            )
            _raise_canvas_error(enrollments_response, "enrollments")
            enrollments = enrollments_response.json()
    except httpx.TimeoutException:
        return "Error: Canvas request timed out."
    except httpx.HTTPError as exc:
        return f"Error requesting Canvas enrollments: {exc}"
    except ValueError:
        return "Error: Canvas returned invalid JSON."

    if not isinstance(courses, list) or not isinstance(enrollments, list):
        return "Error: Canvas returned an unexpected courses or enrollments response."

    course_by_id = {
        course.get("id"): course
        for course in courses
        if isinstance(course, dict) and course.get("id") is not None
    }

    matching_enrollments = {}
    for enrollment in enrollments:
        if not isinstance(enrollment, dict):
            continue
        course_id = enrollment.get("course_id")
        if _matches_prefix(course_by_id.get(course_id), prefix):
            existing = matching_enrollments.get(course_id)
            if existing is None or _has_score(enrollment) and not _has_score(existing):
                matching_enrollments[course_id] = enrollment

    grades = []
    try:
        with httpx.Client(headers=headers, timeout=REQUEST_TIMEOUT) as client:
            for course_id, enrollment in matching_enrollments.items():
                course = course_by_id[course_id]
                assignments = _get_assignments(client, base_url, course_id)
                groups = _get_assignment_groups(client, base_url, course_id)
                syllabus = _get_syllabus(client, base_url, course_id)
                grades.append(_format_course(course, enrollment, assignments, groups, syllabus))
    except httpx.TimeoutException:
        return "Error: Canvas request timed out while loading course details."
    except httpx.HTTPError as exc:
        return f"Error requesting Canvas course details: {exc}"
    except ValueError:
        return "Error: Canvas returned invalid course detail JSON."

    if not grades:
        return f"No Canvas courses found with course code prefix '{prefix}'."

    grades.sort()
    return (
        "course | grade | for A\n"
        "--- | --- | ---\n"
        + "\n".join(grades)
    )


def get_weekly_assignments(course_prefix: str = "FA26") -> str:
    """Return unfinished Canvas assignments due from today through Saturday."""
    if not CANVAS_API_TOKEN:
        return "Error: CANVAS_API_TOKEN is not configured."
    if not course_prefix or not course_prefix.strip():
        return "Error: 'course_prefix' cannot be empty."

    prefix = course_prefix.strip().upper()
    base_url = CANVAS_API_URL.rstrip("/")
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    today = datetime.now().astimezone().date()
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    week_end = week_start + timedelta(days=6)

    try:
        with httpx.Client(headers=headers, timeout=REQUEST_TIMEOUT) as client:
            response = client.get(
                f"{base_url}/users/self/courses",
                params={"enrollment_state": "active", "per_page": 100},
            )
            _raise_canvas_error(response, "courses")
            courses = response.json()
            if not isinstance(courses, list):
                return "Error: Canvas returned an unexpected courses response."

            tasks = []
            for course in courses:
                if not _matches_prefix(course, prefix):
                    continue
                course_id = course.get("id") if isinstance(course, dict) else None
                if course_id is None:
                    continue
                assignments = _get_assignments(client, base_url, course_id)
                course_name = _display_course_name(
                    str(course.get("course_code") or ""),
                    str(course.get("name") or "Unknown course"),
                )
                for assignment in assignments:
                    if _is_open_assignment(assignment):
                        due_date = _assignment_due_date(
                            assignment, today, week_end
                        )
                        if due_date is not None:
                            tasks.append(
                                _format_task(course_name, assignment, due_date)
                            )
    except httpx.TimeoutException:
        return "Error: Canvas request timed out while loading weekly assignments."
    except httpx.HTTPError as exc:
        return f"Error requesting Canvas weekly assignments: {exc}"
    except ValueError:
        return "Error: Canvas returned invalid weekly assignment data."

    if not tasks:
        return f"No unfinished assignments due from {today.isoformat()} through {week_end.isoformat()}."
    tasks.sort()
    return "course | assignment | due\n--- | --- | ---\n" + "\n".join(tasks)


def _is_open_assignment(assignment: object) -> bool:
    if not isinstance(assignment, dict):
        return False
    submission = assignment.get("submission")
    if not isinstance(submission, dict):
        return True
    return not any(
        submission.get(field)
        for field in ("submitted_at", "graded_at", "workflow_state")
        if field != "workflow_state"
    ) and submission.get("workflow_state") not in {"submitted", "graded"}


def _assignment_due_date(
    assignment: dict,
    today,
    week_end,
):
    due_values = [assignment.get("due_at")]
    due_values.extend(
        item.get("due_at")
        for item in assignment.get("all_dates", [])
        if isinstance(item, dict)
    )
    due_dates = []
    for value in due_values:
        if not value:
            continue
        try:
            due_dates.append(datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().date())
        except (TypeError, ValueError):
            continue
    eligible = [date for date in due_dates if today <= date <= week_end]
    return min(eligible) if eligible else None


def _format_task(course_name: str, assignment: dict, due_date) -> str:
    name = str(assignment.get("name") or "Unnamed assignment").replace("|", "/")
    return f"{course_name} | {name} | {due_date.isoformat()}"


def _get_assignments(client: httpx.Client, base_url: str, course_id: object) -> list:
    response = client.get(
        f"{base_url}/courses/{course_id}/assignments",
        params={"per_page": 100, "include[]": "submission"},
    )
    _raise_canvas_error(response, "assignments")
    assignments = response.json()
    if not isinstance(assignments, list):
        raise ValueError("assignments response is not a list")
    return assignments


def _get_syllabus(client: httpx.Client, base_url: str, course_id: object) -> str:
    response = client.get(
        f"{base_url}/courses/{course_id}",
        params={"include[]": "syllabus_body"},
    )
    _raise_canvas_error(response, "syllabus")
    course = response.json()
    if not isinstance(course, dict):
        raise ValueError("course response is not an object")
    return str(course.get("syllabus_body") or "")


def _get_assignment_groups(client: httpx.Client, base_url: str, course_id: object) -> list:
    response = client.get(
        f"{base_url}/courses/{course_id}/assignment_groups",
        params={"per_page": 100},
    )
    _raise_canvas_error(response, "assignment groups")
    groups = response.json()
    if not isinstance(groups, list):
        raise ValueError("assignment groups response is not a list")
    return groups


def _raise_canvas_error(response: httpx.Response, resource: str) -> None:
    if response.status_code == 401:
        raise httpx.HTTPStatusError(
            "Canvas rejected the token (HTTP 401).",
            request=response.request,
            response=response,
        )
    if response.status_code == 403:
        raise httpx.HTTPStatusError(
            f"Canvas denied access to {resource} (HTTP 403).",
            request=response.request,
            response=response,
        )
    response.raise_for_status()


def _matches_prefix(course: object, prefix: str) -> bool:
    if not isinstance(course, dict):
        return False
    course_code = str(course.get("course_code") or "").strip().upper()
    return (
        course_code.startswith(prefix)
        and ("COMPSCI" in course_code or "MATH" in course_code)
    )


def _format_course(
    course: dict,
    enrollment: dict,
    assignments: list,
    groups: list,
    syllabus: str,
) -> str:
    course_code = str(course.get("course_code") or "Unknown course")
    course_name = _display_course_name(course_code, str(course.get("name") or "Unnamed course"))
    earned, distributed, _ = _calculate_progress(assignments, groups)
    canvas_score = _enrollment_current_score(enrollment)
    if canvas_score is not None and distributed:
        earned = distributed * canvas_score / 100
    a_threshold = _find_a_threshold(syllabus) or 93.0
    lost = max(0, distributed - earned)
    allowable_loss = max(0, 100.0 - a_threshold)
    remaining_margin = max(0, allowable_loss - lost)
    return f"{course_name} | {earned:.2f}/{distributed:.2f} | {remaining_margin:.2f}/{allowable_loss:.2f}"


def _display_course_name(course_code: str, fallback: str) -> str:
    match = re.search(r"\b(COMPSCI|MATH)\s*(\d{3})\b", course_code, re.IGNORECASE)
    if match:
        return f"{match.group(1).upper()} {match.group(2)}"
    return fallback


def _enrollment_current_score(enrollment: dict) -> float | None:
    grades = enrollment.get("grades")
    if not isinstance(grades, dict):
        return None
    return _number(grades.get("current_score"))


def _calculate_progress(assignments: list, groups: list) -> tuple[float, float, float]:
    """Calculate final-scale points earned, distributed, and total possible."""
    valid = [
        assignment for assignment in assignments
        if isinstance(assignment, dict)
        and _number(assignment.get("points_possible")) is not None
        and not assignment.get("omit_from_final_grade")
    ]
    group_weights = {
        group.get("id"): _number(group.get("group_weight"))
        for group in groups
        if isinstance(group, dict) and _number(group.get("group_weight")) is not None
    }
    weighted = bool(group_weights) and sum(group_weights.values()) > 0
    graded = [
        item for item in valid
        if isinstance(item.get("submission"), dict)
        and item["submission"].get("score") is not None
        and not item["submission"].get("excused")
    ]
    if weighted:
        earned = distributed = 0.0
        for group_id, weight in group_weights.items():
            group_items = [item for item in valid if item.get("assignment_group_id") == group_id]
            group_graded = [item for item in graded if item.get("assignment_group_id") == group_id]
            group_total = sum(_number(item["points_possible"]) or 0 for item in group_items)
            if not group_total:
                continue
            group_possible = sum(_number(item["points_possible"]) or 0 for item in group_graded)
            group_earned = sum(
                min(max(_number(item["submission"].get("score")) or 0, 0), _number(item["points_possible"]) or 0)
                for item in group_graded
            )
            earned += (group_earned / group_total) * (weight or 0)
            distributed += (group_possible / group_total) * (weight or 0)
        return earned, distributed, 100.0

    total_possible = sum(_number(item["points_possible"]) or 0 for item in valid)
    graded_possible = sum(_number(item["points_possible"]) or 0 for item in graded)
    earned_raw = sum(
        min(max(_number(item["submission"].get("score")) or 0, 0), _number(item["points_possible"]) or 0)
        for item in graded
    )
    if not total_possible:
        return 0.0, 0.0, 0.0
    return earned_raw / total_possible * 100, graded_possible / total_possible * 100, 100.0


def _number(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _find_a_threshold(syllabus: str) -> float | None:
    text = html.unescape(re.sub(r"<[^>]+>", " ", syllabus))
    patterns = (
        r"\bA\s*(?:grade|:)?\s*(?:is|=|requires?)?\s*(\d{2,3}(?:\.\d+)?)\s*%",
        r"\bA\s*[-–]\s*(\d{2,3}(?:\.\d+)?)\s*%",
        r"\bA\s*(?:>=|≥)\s*(\d{2,3}(?:\.\d+)?)\s*%",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            threshold = float(match.group(1))
            if 0 <= threshold <= 100:
                return threshold
    return None


def _has_score(enrollment: dict) -> bool:
    grades = enrollment.get("grades")
    if not isinstance(grades, dict):
        return False
    return grades.get("current_score") is not None or grades.get("final_score") is not None
