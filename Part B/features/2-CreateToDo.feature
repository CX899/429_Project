Feature: Create a ToDo
  As a user, I want to create a new ToDo so that I can keep track of tasks.

  Background:
    Given the system is running
  # Normal Flow

  Scenario Outline: Create a ToDo with valid data
    Given the user has a valid JSON body for a new ToDo with:
      | title   | doneStatus   | description   |
      | <title> | <doneStatus> | <description> |
    When the user sends a POST request to "/todos" with this JSON body
    Then the response status should be 201
    And the response JSON should contain a new ToDo with the specified title, doneStatus, and description
    And the response JSON should contain a unique "id"

    Examples:
      | title           | doneStatus | description             |
      | "Buy groceries" | false      | "Milk, eggs, and bread" |
  # Alternate Flow

  Scenario Outline: Create a ToDo without specifying an ID
    Given the user has a valid JSON body for a new ToDo without an "id" field:
      | title   | doneStatus   | description   |
      | <title> | <doneStatus> | <description> |
    When the user sends a POST request to "/todos" with this JSON body
    Then the response status should be 201
    And the response JSON should contain a new ToDo with the specified title, doneStatus, and description
    And the response JSON should contain a newly generated "id" that does not match any existing ToDo

    Examples:
      | title      | doneStatus | description   |
      | "Call mom" | false      | "Weekly call" |
  # Error Flow

  Scenario Outline: Attempt to create a ToDo with invalid or missing fields
    Given the user has an invalid JSON body for a new ToDo with "<issue>"
    When the user sends a POST request to "<endpoint>"
    Then the response status should be <status>
    And <assertion>

    Examples:
      | issue                               | endpoint                | status | assertion                                                   |
      | "missing required fields"           | /todos                  | 400    | the response JSON should contain an error message indicating invalid input |
      | "title is null"                     | /todos                  | 400    | the response JSON should contain an error message indicating invalid input |
      | "doneStatus is not a boolean value" | /todos                  | 400    | the response JSON should contain an error message indicating invalid input |
      | "bug: post to existing todo"        | /todos/1                | 405    | the response should include an error message about method not allowed      |