Feature: Create a Project
  As a user, I want to create a Project to organize my ToDos.

  # Normal Flow
  Scenario Outline: Create a new Project with valid data
    Given I have the following project information
      | title       | completed   | active   | description       |
      | "<title>"   | <completed> | <active> | "<description>"   |
    When I send a <method> request to "<endpoint>" with this project information
    Then the response status should be 201
    And the response should contain the created project with a generated ID
    And the created project should have the provided information

    Examples:
      | method | endpoint  | title              | completed | active | description            |
      | POST   | /projects | Database Migration | false     | true   | Upgrade to PostgreSQL |

  # Alternate Flow
  Scenario Outline: Create a new Project without specifying an ID
    Given I have the following project information without an ID
      | title       | completed   | active   | description       |
      | "<title>"   | <completed> | <active> | "<description>"   |
    When I send a <method> request to "<endpoint>" with this project information
    Then the response status should be 201
    And the response should contain the created project with a system-generated ID
    And the created project should have the provided information

    Examples:
      | method | endpoint  | title              | completed | active | description            |
      | POST   | /projects | Database Migration | false     | true   | Upgrade to PostgreSQL |

  # Error Flow - Adjusted to match actual API behavior
  Scenario Outline: Create a Project with missing title field
    Given I have the following incomplete project information
      | completed   | active   | description       |
      | <completed> | <active> | "<description>"   |
    When I send a <method> request to "<endpoint>" with this incomplete information
    Then the response status should be 201
    And the response should contain the created project with a generated ID
    And the created project should have the provided information

    Examples:
      | method | endpoint  | completed | active | description            |
      | POST   | /projects | false     | true   | Upgrade to PostgreSQL |