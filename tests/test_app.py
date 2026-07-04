import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as app_activities


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(app_activities)
    app_activities.clear()
    app_activities.update(copy.deepcopy(original))
    yield
    app_activities.clear()
    app_activities.update(copy.deepcopy(original))


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"][0] == "michael@mergington.edu"


def test_signup_for_activity_adds_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Signed up newstudent@mergington.edu for Chess Club"
    assert "newstudent@mergington.edu" in app_activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_remove_participant_removes_existing_student(client):
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Removed michael@mergington.edu from Chess Club"
    assert "michael@mergington.edu" not in app_activities["Chess Club"]["participants"]


def test_remove_participant_fails_for_missing_student(client):
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "missing@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"
