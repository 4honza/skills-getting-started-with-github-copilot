import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    # Deep-copy the activities before each test and restore after to keep tests isolated
    backup = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(backup))


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # Expect some known activities from the initial dataset
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_and_remove_participant(client):
    email = "tester@example.com"
    activity = "Programming Class"

    # Ensure not present
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]

    # Sign up
    signup_url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    resp = client.post(signup_url)
    assert resp.status_code == 200
    assert "Signed up" in resp.json()["message"]

    # Now participant should appear
    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]

    # Remove participant
    delete_url = f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(email)}"
    resp = client.delete(delete_url)
    assert resp.status_code == 200
    assert "Removed" in resp.json()["message"]

    # Now should be gone
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_signup_duplicate_fails(client):
    email = "dup@example.com"
    activity = "Programming Class"

    signup_url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    resp = client.post(signup_url)
    assert resp.status_code == 200

    # Signing up again (even for another activity) should fail due to global check
    resp = client.post(signup_url)
    assert resp.status_code == 400


def test_delete_nonexistent_participant_returns_404(client):
    email = "nobody@example.com"
    activity = "Programming Class"
    delete_url = f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(email)}"
    resp = client.delete(delete_url)
    assert resp.status_code == 404


def test_signup_nonexistent_activity_returns_404(client):
    email = "noact@example.com"
    activity = "No Such Activity"
    signup_url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    resp = client.post(signup_url)
    assert resp.status_code == 404
