Feature: Create a Category
  As a user, I want to create a Category to organize my ToDos.

  Background:
    Given the system has been reset to its initial state
    And the system contains the following categories:
      | id | title      | description          |
      |  1 | "Work"     | "Work related tasks" |
      |  2 | "Personal" | "Personal tasks"     |
  # Normal Flow

  Scenario Outline: Create a new Category with valid data
    Given I have the following category data:
      | title   | description   |
      | <title> | <description> |
    When the user sends a POST request to "/categories" with this data
    Then the response status should be 201
    And the response JSON should include a newly created category with the provided data
    And the category should have a system-generated unique ID

    Examples:
      | title       | description          |
      | "Fitness"   | "Exercise goals"     |
      | "Education" | "Learning materials" |
  # Error Flow

  Scenario Outline: Attempt to create a Category with missing required fields
    Given I have incomplete category data missing "<missing_field>"
    When the user sends a POST request to "/categories" with this incomplete data
    Then the response status should be <expected_status>
    And the response JSON should <validation_action>

    Examples:
      | missing_field | expected_status | validation_action                                  |
      | "title"       | 400             | include an error message indicating missing required fields |