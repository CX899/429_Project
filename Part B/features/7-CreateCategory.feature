Feature: Create a Category
  As a user I want to create a Category to organize my ToDos.

  Background:
    Given the system contains the following categories
      | id | title              | description           |
      | 1  | "Work"             | "Work related tasks"  |
      | 2  | "Personal"         | "Personal tasks"      |

  # Normal Flow
  Scenario: Create a new Category with valid data
    Given I have the following category data
      | title     | description       |
      | "Fitness" | "Exercise goals"  |
    When I send a POST request to "/categories" with the category data
    Then the response status should be 201
    And the response JSON should include a newly created category with the provided data
    And the category should have a unique ID
    
  # Alternate Flow
  Scenario: Create a new Category without specifying an ID
    Given I have the following category data without an ID
      | title      | description          |
      | "Education" | "Learning materials" |
    When I send a POST request to "/categories" with the category data
    Then the response status should be 201
    And the response JSON should include a newly created category with the provided data
    And the category should have a system-generated unique ID

  # Error Flow
  Scenario: Create a Category with missing required fields
    Given I have the following incomplete category data
      | description           |
      | "Incomplete category" |
    When I send a POST request to "/categories" with the incomplete data
    Then the response status should be 400
    And the response should include an error message indicating missing required fields