Feature: Create a ToDo
  As a user, I want to create a new ToDo so that I can keep track of a task.

  Background:
    Given the system is running with no specific todos initially
  # Normal Flow

  Scenario: Create a ToDo with a valid body
    When the user sends a POST request to "/todos" with a valid JSON body:
      | title       | "Buy groceries"     |
      | description | "Milk, eggs, bread" |
      | doneStatus  | false               |
    Then the response status should be 201
    And the response JSON should indicate a successful creation of the ToDo
    And the response JSON should contain:
      | title       | "Buy groceries"     |
      | description | "Milk, eggs, bread" |
      | doneStatus  | false               |
  # Alternate Flow

  Scenario: Create a ToDo without specifying an ID
    When the users send a POST request to "/todos" with the following JSON body:
      | title       | "Finish assignment" |
      | description | "Due tomorrow"      |
      | doneStatus  | false               |
    Then the response status should be 201
    And the response JSON should show a newly generated unique ID for the todo
    And the response JSON should contain:
      | title       | "Finish assignment" |
      | description | "Due tomorrow"      |
      | doneStatus  | false               |
  # Error Flow

  Scenario: Create a ToDo with an invalid body
    When the user sends a POST request to "/todos" with the following JSON body:
      | title | "" |
    Then the response status should be 400
    And the response JSON should contain an error message "Invalid todo data"
