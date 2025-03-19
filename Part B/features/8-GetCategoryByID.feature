Feature: Get Category By ID
  As a user, I want to get a specific Category by its ID to view its details.

  Background:
    Given the system has been reset to its initial state
    And the system contains the following categories:
      | id | title      | description          |
      | 1  | "Work"     | "Work related tasks" |
      | 2  | "Personal" | "Personal tasks"     |
      | 3  | "Shopping" | "Items to purchase"  |

  # Normal Flow
  Scenario Outline: Retrieve a Category by its ID
    When the user sends a GET request to "/categories/<id>"
    Then the response status should be 200
    And the response should contain the category with ID "<id>"

    Examples:
      | id |
      | 1  |
      | 2  |
      | 3  |

  # Alternate Flow
  Scenario: Retrieve a non-existent Category
    When the user sends a GET request to "/categories/9999"
    Then the response status should be 404
    And the response JSON should contain an error message mentioning "Could not find an instance with categories/9999"

  # Error Flow
  Scenario Outline: Retrieve a Category with an invalid ID format
    When the user sends a GET request to "/categories/<id>"
    Then the response status should be 404
    And the response JSON should contain an error message mentioning "Could not find an instance with categories/<id>"
    
    Examples:
      | id     |
      | abc    |
      | 123abc |