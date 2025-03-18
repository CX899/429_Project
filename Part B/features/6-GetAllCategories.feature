Feature: Get All Categories
  As a User I want to get all Categories so I can view them.

  Background:
    Given the system contains the following categories
      | id | title              | description           |
      | 1  | "Work"             | "Work related tasks"  |
      | 2  | "Personal"         | "Personal tasks"      |
      | 3  | "Shopping"         | "Items to purchase"   |

  # Normal Flow
  Scenario: Retrieve all Categories
    When I send a GET request to "/categories"
    Then the response status should be 200
    And the response JSON should include the following categories:
      | id | title              | description           |
      | 1  | "Work"             | "Work related tasks"  |
      | 2  | "Personal"         | "Personal tasks"      |
      | 3  | "Shopping"         | "Items to purchase"   |

  # Alternate Flow
  Scenario Outline: Retrieve filtered Categories
    Given a filter where "<filter_key>" equals "<filter_value>"
    When I send a GET request to "/categories?<filter_key>=<filter_value>"
    Then the response status should be 200
    And the response JSON should contain only categories where <filter_key> equals "<filter_value>"
    Examples:
      | filter_key  | filter_value     |
      | title       | "Work"           |
      | description | "Personal tasks" |

  # Error Flow
  Scenario: Unsupported request method for categories endpoint
    When I send a PATCH request to "/categories"
    Then the response status should be 405
    And the response should include an error message indicating method not allowed