import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test (Arrange phase)"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 3,
            "participants": ["john@mergington.edu"]
        }
    })
    yield
    activities.clear()


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_all_activities_success(self, client):
        """Test successfully retrieving all activities"""
        # Arrange: Activities are pre-loaded via fixture
        
        # Act: Make GET request
        response = client.get("/activities")
        
        # Assert: Verify response and data
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_contains_correct_fields(self, client):
        """Test that each activity has required fields"""
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert set(activity_data.keys()) == expected_fields

    def test_get_activities_participants_count(self, client):
        """Test that participants list is correct"""
        # Arrange
        expected_chess_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert data["Chess Club"]["participants"] == expected_chess_participants


class TestSignup:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_success(self, client):
        """Test successfully signing up a new student"""
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_count = len(activities[activity]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert len(activities[activity]["participants"]) == initial_count + 1
        assert email in activities[activity]["participants"]

    def test_signup_duplicate_email_fails(self, client):
        """Test that duplicate signup is rejected"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_invalid_activity_fails(self, client):
        """Test signup for non-existent activity"""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_activity_full_fails(self, client):
        """Test signup when activity is at max capacity"""
        # Arrange: Gym Class has max_participants=3, currently has 1
        activity = "Gym Class"
        emails = ["student1@mergington.edu", "student2@mergington.edu"]
        
        # Act: Fill activity to capacity
        for email in emails:
            client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act: Try to signup when full
        response = client.post(
            f"/activities/{activity}/signup?email=student3@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()

    def test_signup_multiple_students_success(self, client):
        """Test multiple students can sign up for different activities"""
        # Arrange
        signups = [
            ("Chess Club", "alice@mergington.edu"),
            ("Programming Class", "bob@mergington.edu"),
            ("Gym Class", "charlie@mergington.edu")
        ]
        
        # Act: Sign up all students
        for activity, email in signups:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            # Assert: Each signup succeeds
            assert response.status_code == 200
        
        # Assert: All signups are recorded
        response = client.get("/activities")
        data = response.json()
        assert "alice@mergington.edu" in data["Chess Club"]["participants"]
        assert "bob@mergington.edu" in data["Programming Class"]["participants"]
        assert "charlie@mergington.edu" in data["Gym Class"]["participants"]


class TestUnregister:
    """Test suite for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_success(self, client):
        """Test successfully unregistering an existing participant"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(activities[activity]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert len(activities[activity]["participants"]) == initial_count - 1
        assert email not in activities[activity]["participants"]

    def test_unregister_not_registered_fails(self, client):
        """Test unregister for student not registered"""
        # Arrange
        activity = "Chess Club"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_invalid_activity_fails(self, client):
        """Test unregister from non-existent activity"""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_all_participants_success(self, client):
        """Test unregistering all participants from an activity"""
        # Arrange
        activity = "Chess Club"
        emails = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act: Unregister all
        for email in emails:
            response = client.delete(
                f"/activities/{activity}/unregister?email={email}"
            )
            # Assert: Each unregister succeeds
            assert response.status_code == 200
        
        # Assert: Activity has no participants
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == 0

    def test_unregister_then_signup_success(self, client):
        """Test that unregistered student can sign up again"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act: Unregister
        response1 = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        # Assert: Unregister succeeds
        assert response1.status_code == 200
        
        # Act: Sign up again
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        # Assert: Signup succeeds
        assert response2.status_code == 200
        assert email in activities[activity]["participants"]
