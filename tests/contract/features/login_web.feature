Feature: Login web contract
  The shared web step library actually drives the bundled mock's HTML page.

  Scenario: Show error for bad credentials
    Given I am on the "login" page
    When I fill in "email" with "bad@user.com"
    And I fill in "password" with "wrong"
    And I click "submit"
    Then the "error" has text "Invalid credentials"
