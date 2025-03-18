Feature: Delete a ToDo Given an ID
  As a user I want to delete a specific ToDo in order to remove it from my ToDos.

  Background:
    Given the system contains the following todos
      | id | title               | doneStatus | description         |
      |  1 | "Buy groceries"     | false      | "Milk, eggs, bread" |
      |  2 | "Call mom"          | false      | "Weekly call"       |
      |  3 | "Finish assignment" | false      | "Due tomorrow"      |

  # Normal Flow
  Scenario: Successfully delete a ToDo
    When I send a DELETE request to "/todos/2"
    Then the response status should be 200
    And the todo with id "2" should no longer exist in the system
    And when I send a GET request to "/todos"
    Then the response JSON should include only the following todos:
      | id | title               | doneStatus | description         |
      |  1 | "Buy groceries"     | false      | "Milk, eggs, bread" |
      |  3 | "Finish assignment" | false      | "Due tomorrow"      |

  # Alternate Flow
  Scenario: Attempt to delete a non-existing ToDo
    When I send a DELETE request to "/todos/99"
    Then the response status should be 404
    And the response should include an error message indicating "Todo not found"
    And the system should still contain all original todos

  # Error Flow
  Scenario Outline: Attempt to delete a ToDo with invalid ID format
    When I send a DELETE request to "/todos/<invalid_id>"
    Then the response status should be 400
    And the response should include an error message about invalid ID format
    And the system should still contain all original todos

    Examples:
      | invalid_id   |
      | "abc"        |
      | "-1"         |
      | "!@#$"       |