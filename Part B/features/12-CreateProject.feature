Feature: Create a Project
  As a user, I want to create a Project to organize my ToDos.

  # Normal Flow
  Scenario: Create a new Project with valid data
    Given I have the following project information
      | title              | completed | active | description               |
      | "Database Migration" | false     | true   | "Upgrade to PostgreSQL" |
    When I send a POST request to "/projects" with this project information
    Then the response status should be 201
    And the response should contain the created project with a generated ID
    And the created project should have the provided information

  # Alternate Flow
  Scenario: Create a new Project without specifying an ID
    Given I have the following project information without an ID
      | title              | completed | active | description               |
      | "Database Migration" | false     | true   | "Upgrade to PostgreSQL" |
    When I send a POST request to "/projects" with this project information
    Then the response status should be 201
    And the response should contain the created project with a system-generated ID
    And the created project should have the provided information

  # Error Flow
  Scenario: Attempt to create a Project with missing required fields
    Given I have the following incomplete project information
      | completed | active | description               |
      | false     | true   | "Upgrade to PostgreSQL" |
    When I send a POST request to "/projects" with this incomplete information
    Then the response status should be 400
    And the response should contain validation errors