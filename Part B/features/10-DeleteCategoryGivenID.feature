Feature: Delete a Category Given an ID
  As a user, I want to delete a specific Category to remove it and its purpose as an organizer.

  Background:
    Given the system contains the following categories
      | id | title      | description          |
      | 1  | "Work"     | "Work related tasks" |
      | 2  | "Personal" | "Personal tasks"     |
      | 3  | "Shopping" | "Items to purchase"  |

  # Normal Flow
  Scenario Outline: Delete an existing Category
    When I send a <method> request to "/categories/<id>"
    Then the response status should be 204
    When I send a GET request to "/categories/<id>"
    Then the response status should be 404

    Examples:
      | method | id |
      | DELETE | 3  |

  # Alternate Flow
  Scenario Outline: Delete a non-existing Category
    When I send a <method> request to "/categories/<id>"
    Then the response status should be 404
    And the response should include an error message indicating category not found

    Examples:
      | method | id |
      | DELETE | 99 |

  # Error Flow
  Scenario Outline: Delete a Category with invalid ID format
    When I send a <method> request to "/categories/<invalid_id>"
    Then the response status should be 404
    And the response should include an error message indicating invalid ID format

    Examples:
      | method | invalid_id |
      | DELETE | abc        |