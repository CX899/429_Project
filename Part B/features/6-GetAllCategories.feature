Feature: Get All Categories
  As a user, I want to get all Categories so I can view them.

  Background:
    Given the system has been reset to its initial state
    And the system contains the following categories:
      | id | title      | description          |
      |  1 | "Work"     | "Work related tasks" |
      |  2 | "Personal" | "Personal tasks"     |
      |  3 | "Shopping" | "Items to purchase"  |
  # Normal Flow

  Scenario: Retrieve all Categories successfully
    When the user sends a GET request to "/categories"
    Then the response status should be 200
    And the response JSON should include the following categories:
      | id | title      | description          |
      |  1 | "Work"     | "Work related tasks" |
      |  2 | "Personal" | "Personal tasks"     |
      |  3 | "Shopping" | "Items to purchase"  |
  # Alternate Flow

  Scenario Outline: Retrieve filtered Categories based on "<filter_key>"
    Given the user filters categories where "<filter_key>" equals "<filter_value>"
    When the user sends a GET request to "/categories?<filter_key>=<filter_value>"
    Then the response status should be 200
    And the response JSON should contain only categories where "<filter_key>" equals "<filter_value>"

    Examples:
      | filter_key  | filter_value     |
      | title       | "Work"           |
      | description | "Personal tasks" |
  # Error Flow

  Scenario Outline: Unsupported request methods for the categories endpoint
    When the user sends a <method> request to "/categories"
    Then the response status should be 405
    And the response JSON should contain an error message "Method not allowed"

    Examples:
      | method |
      | PATCH  |
      | PUT    |
      | DELETE |
