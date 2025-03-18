Feature: Delete a ToDo by ID
  As a user, I want to delete a specific ToDo in order to remove it from my ToDos.

  Background: Server is running with ToDos
    Given the system has been reset to its initial state
    And the system contains the following todos:
      | id | title           | doneStatus | description         |
      |  1 | "Buy groceries" | false      | "Milk, eggs, bread" |
      |  2 | "Call mom"      | false      | "Weekly call"       |
  # Normal Flow

  Scenario Outline: Successfully delete an existing ToDo
    Given a ToDo with ID equal to <id> exists
    When the user sends a DELETE request to "/todos/<id>"
    Then the ToDo with id <id> is successfully deleted
    And the user is notified of the completion of the deletion operation

    Examples:
      | id |
      |  1 |
      |  2 |
  # Alternate Flow

  Scenario Outline: Attempt to delete a non-existing ToDo
    Given a ToDo with ID equal to <id> does not exist
    When the user sends a DELETE request to "/todos/<id>"
    Then the response status should be 404
    And the response JSON should contain an error message <message>

    Examples:
      | id   | message          |
      | 9999 | "ToDo not found" |
      | 5000 | "ToDo not found" |
  # Error Flow

  Scenario Outline: Delete a ToDo with an invalid ID
    Given a ToDo with ID equal to <id> does not exist or the ID format is invalid
    When the user sends a DELETE request to "/todos/<id>"
    Then the response status should be 400
    And the response JSON should contain an error message <message>

    Examples:
      | id     | message                                        |
      | abc    | "Could not find an instance with todos/abc"    |
      | 123abc | "Could not find an instance with todos/123abc" |
