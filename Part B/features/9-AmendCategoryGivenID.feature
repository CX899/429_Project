Feature: Amend a Category Given an ID
  As a user I want to amend a specific Category to update its details.

  Background:
    Given the system contains the following categories
      | id | title              | description           |
      | 1  | "Work"             | "Work related tasks"  |
      | 2  | "Personal"         | "Personal tasks"      |
      | 3  | "Shopping"         | "Items to purchase"   |

  # Normal Flow
  Scenario: Update a Category with complete new data
    Given I have the following updated category data
      | title          | description               |
      | "Work Projects" | "Professional activities" |
    When I send a PUT request to "/categories/1" with the updated data
    Then the response status should be 200
    And the response JSON should include the following updated category:
      | id | title           | description                |
      | 1  | "Work Projects" | "Professional activities"  |

  # Alternate Flow
  Scenario: Update only specific fields of a Category
    Given I have the following partial category data
      | description       |
      | "Daily routines"  |
    When I send a PUT request to "/categories/2" with the partial data
    Then the response status should be 200
    And the response JSON should include the following updated category:
      | id | title      | description      |
      | 2  | "Personal" | "Daily routines" |

  # Error Flow
  Scenario: Update a Category with invalid ID
    Given I have the following updated category data
      | title      | description     |
      | "Updated"  | "New desc"      |
    When I send a PUT request to "/categories/abc" with the updated data
    Then the response status should be 400
    And the response should include an error message indicating invalid ID format