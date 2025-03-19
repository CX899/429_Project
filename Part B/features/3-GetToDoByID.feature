Feature: Get a ToDo by ID
  As a user, I want to get a specific ToDo to view so that I can check its details.

  Background:
    Given the system contains the following todos
      | id | title           | doneStatus | description         |
      |  1 | "Buy groceries" | false      | "Milk, eggs, bread" |
      |  2 | "Call mom"      | false      | "Weekly call"       |
  # Normal Flow

  Scenario Outline: Retrieve a ToDo with a valid existing ID
    When the user sends a GET request to "/todos/<id>"
    Then the response status should be 200
    And the response JSON should contain a todo with id "<id>"

    Examples:
      | id |
      |  1 |
      |  2 |
  # Alternate Flow

  Scenario: Retrieve a ToDo with a valid formatted ID for a non-existing ToDo
    When the user sends a GET request to "/todos/9999"
    Then the response status should be 404
    And the response JSON should contain an error message mentioning "Could not find an instance with todos/9999"
  # Error Flow

  Scenario Outline: Retrieve a ToDo with an invalid ID format
    Given a ToDo with ID equal to <id> does not exist or the ID format is invalid
    When the user sends a GET request to "/todos/<id>"
    Then the response status should be 404
    And the response JSON should contain an error message mentioning "Could not find an instance with todos/<id>"

    Examples:
      | id     |
      | abc    |
      | 123abc |