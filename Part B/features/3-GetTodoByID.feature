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
    And the response JSON should include the todo with id "<id>" with title "<title>", doneStatus "<doneStatus>" and description "<description>"

    Examples:
      | id | title           | doneStatus | description         |
      |  1 | "Buy groceries" | false      | "Milk, eggs, bread" |
      |  2 | "Call mom"      | false      | "Weekly call"       |
  # Alternate Flow

  Scenario: Retrieve a ToDo with a valid formatted ID for a non-existing ToDo
    When the user sends a GET request to "/todos/9999"
    Then the response status should be 404
    And the response JSON should contain an error message "ToDo not found"
  # Error Flow

  Scenario: Retrieve a ToDo with an invalid ID format (Error Flow)
    Given a ToDo with ID equal to <id> does not exist or the ID format is invalid
    When the user sends a GET request to "/todos/<id>"
    Then the response status should be 400
    And the response JSON should contain an error message <message>

    Examples:
      | id     | message                                        |
      | abc    | "Could not find an instance with todos/abc"    |
      | 123abc | "Could not find an instance with todos/123abc" |
