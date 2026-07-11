Feature: Login API contract
  The shared API step library actually drives the bundled mock.

  Scenario: Reject bad credentials
    Given the API is available
    When I POST credentials "bad@user.com" / "wrong"
    Then the response status is 401
    And the json field "error" equals "Invalid credentials"

  Scenario: Accept valid credentials
    Given the API is available
    When I POST credentials "user@example.com" / "correct-password"
    Then the response status is 200
    And the json field "token" equals "fake-jwt-token"
