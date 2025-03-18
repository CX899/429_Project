Feature: Get a Category Given an ID
  As a User I want to get a specific Category to view it.

  Background:
    Given the system contains the following categories
      | id | title              | description           |
      | 1  | "Work"             | "Work related tasks"  |
      | 2  | "Personal"         | "Personal tasks"      |
      | 3  | "Shopping"         | "Items to purchase"   |

  # Normal Flow
  Scenario: Retrieve a specific Category by ID
    When I send a GET request to "/categories/2"
    Then the response status should be 200
    And the response JSON should include the following category:
      | id | title      | description     |
      | 2  | "Personal" | "Personal tasks" |

  # Alternate Flow
  Scenario: Retrieve a non-existing Category by ID
    When I send a GET request to "/categories/99"
    Then the response status should be 404
    And the response should include an error message indicating category not found

  # Error Flow
  Scenario: Retrieve a Category with invalid ID format
    When I send a GET request to "/categories/abc"
    Then the response status should be 400
    And the response should include an error message indicating invalid ID format