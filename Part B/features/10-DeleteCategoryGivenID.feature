Feature: Delete a Category Given an ID
  As a user I want to delete a specific Category to remove it and its purpose as an organizer.

  Background:
    Given the system contains the following categories
      | id | title              | description           |
      | 1  | "Work"             | "Work related tasks"  |
      | 2  | "Personal"         | "Personal tasks"      |
      | 3  | "Shopping"         | "Items to purchase"   |

  # Normal Flow
  Scenario: Delete an existing Category
    When I send a DELETE request to "/categories/3"
    Then the response status should be 204
    And when I send a GET request to "/categories"
    Then the response should not include a category with id "3"

  # Alternate Flow
  Scenario: Delete a non-existing Category
    When I send a DELETE request to "/categories/99"
    Then the response status should be 404
    And the response should include an error message indicating category not found

  # Error Flow
  Scenario: Delete a Category with invalid ID format
    When I send a DELETE request to "/categories/abc"
    Then the response status should be 400
    And the response should include an error message indicating invalid ID format