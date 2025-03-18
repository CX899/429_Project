Feature: Create a ToDo
  As a user, I want to create a new ToDo so that I can keep track of tasks.

  Background:
    Given the system is running
  # Normal Flow

  Scenario: Create a ToDo with valid data
    Given I have a valid JSON body for a new ToDo with:
      | title           | doneStatus | description             |
      | "Buy groceries" | false      | "Milk, eggs, and bread" |
    When I send a POST request to "/todos" with this JSON body
    Then the response status should be 201
    And the response JSON should contain a new ToDo with the specified title, doneStatus, and description
    And the response JSON should contain a unique "id"
  # Alternate Flow

  Scenario: Create a ToDo without specifying an ID
    Given I have a valid JSON body for a new ToDo without an "id" field:
      | title      | doneStatus | description   |
      | "Call mom" | false      | "Weekly call" |
    When I send a POST request to "/todos" with this JSON body
    Then the response status should be 201
    And the response JSON should contain a new ToDo with the specified title, doneStatus, and description
    And the response JSON should contain a newly generated "id" that does not match any existing ToDo
  # Error Flow

  Scenario: Attempt to create a ToDo with invalid or missing fields
    Given I have an invalid JSON body for a new ToDo that is missing required fields
    When I send a POST request to "/todos" with this invalid body
    Then the response status should be 400
    And the response JSON should contain an error message indicating invalid input
