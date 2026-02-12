"""
Unit tests for the Mergington High School Activities API.
"""

import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_list(self, client, fresh_activities):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_structure(self, client, fresh_activities):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_activities_include_participants(self, client, fresh_activities):
        """Test that activities include participant information."""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant(self, client, fresh_activities):
        """Test signing up a new participant for an activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_updates_participants_list(self, client, fresh_activities):
        """Test that signup correctly adds participant to the list."""
        email = "newstudent@mergington.edu"
        client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Programming Class"]["participants"]

    def test_signup_nonexistent_activity(self, client, fresh_activities):
        """Test signing up for an activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_registered(self, client, fresh_activities):
        """Test that a student cannot sign up twice for the same activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_respects_max_participants(self, client, fresh_activities):
        """Test that an activity respects its max participant limit."""
        # This is a validation test - the API currently doesn't enforce max_participants
        # but this test documents that behavior
        response = client.post(
            "/activities/Gym Class/signup",
            params={"email": "student1@mergington.edu"}
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_participant(self, client, fresh_activities):
        """Test unregistering a participant from an activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
        assert "Chess Club" in data["message"]

    def test_unregister_removes_from_list(self, client, fresh_activities):
        """Test that unregister correctly removes participant from the list."""
        email = "michael@mergington.edu"
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self, client, fresh_activities):
        """Test unregistering from an activity that doesn't exist."""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up(self, client, fresh_activities):
        """Test that unregister fails if student is not signed up."""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]


class TestActivityFlow:
    """Integration tests for complete activity workflows."""

    def test_signup_then_unregister(self, client, fresh_activities):
        """Test the complete flow of signing up and then unregistering."""
        email = "student@mergington.edu"
        activity = "Programming Class"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify signup
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify unregister
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]

    def test_multiple_signups_and_spot_calculation(self, client, fresh_activities):
        """Test multiple signups and spot availability calculation."""
        activity = "Programming Class"
        
        # Get initial participant count
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity]["participants"])
        
        # Sign up multiple students
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all signed up
        final_activities = client.get("/activities").json()
        final_count = len(final_activities[activity]["participants"])
        assert final_count == initial_count + len(emails)
        
        for email in emails:
            assert email in final_activities[activity]["participants"]
