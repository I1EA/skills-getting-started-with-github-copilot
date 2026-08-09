import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app, follow_redirects=False)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_static_index_is_available(client):
    # Arrange
    static_index_path = "/static/index.html"

    # Act
    response = client.get(static_index_path)

    # Assert
    assert response.status_code == 200
    assert "Mergington" in response.text


def test_get_activities_returns_activity_contract(client):
    # Arrange
    required_fields = {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert "Soccer Club" in activities
    assert required_fields <= activities["Chess Club"].keys()
    assert isinstance(activities["Chess Club"]["participants"], list)


def test_signup_adds_student_to_activity(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "student@mergington.edu"
    initial_participants = list(app_module.activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert app_module.activities[activity_name]["participants"] == [
        *initial_participants,
        email,
    ]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]