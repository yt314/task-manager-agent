from itertools import count
from typing import Optional

_tasks: list[dict] = []
_next_code = count(1)


def _title_matches(query: str, title: str) -> bool:
    query_words = query.lower().split()
    title_words = title.lower().split()
    return any(qw in tw or tw in qw for qw in query_words for tw in title_words)


def get_tasks(
    code: Optional[int] = None,
    title: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    end_date_from: Optional[str] = None,
    end_date_to: Optional[str] = None,
) -> list[dict]:
    results = _tasks

    if code is not None:
        results = [t for t in results if t["code"] == code]
    if title:
        results = [t for t in results if _title_matches(title, t["title"])]
    if type:
        results = [t for t in results if t["type"] == type]
    if status:
        results = [t for t in results if t["status"] == status]
    if start_date_from:
        results = [t for t in results if t["start_date"] and t["start_date"] >= start_date_from]
    if start_date_to:
        results = [t for t in results if t["start_date"] and t["start_date"] <= start_date_to]
    if end_date_from:
        results = [t for t in results if t["end_date"] and t["end_date"] >= end_date_from]
    if end_date_to:
        results = [t for t in results if t["end_date"] and t["end_date"] <= end_date_to]

    return results


def add_task(
    title: str,
    description: str = "",
    type: str = "task",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: str = "pending",
) -> dict:
    task = {
        "code": next(_next_code),
        "title": title,
        "description": description,
        "type": type,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
    }
    _tasks.append(task)
    return task


def update_task(
    code: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
) -> Optional[dict]:
    for task in _tasks:
        if task["code"] == code:
            if title is not None:
                task["title"] = title
            if description is not None:
                task["description"] = description
            if type is not None:
                task["type"] = type
            if start_date is not None:
                task["start_date"] = start_date
            if end_date is not None:
                task["end_date"] = end_date
            if status is not None:
                task["status"] = status
            return task
    return None


def delete_task(code: int) -> bool:
    for i, task in enumerate(_tasks):
        if task["code"] == code:
            del _tasks[i]
            return True
    return False
