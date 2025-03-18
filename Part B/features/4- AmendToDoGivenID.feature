Feature: Amend a ToDo Details
  As a user, I want to amend a specific ToDo in order to update its details.

  Background: Server is running and ToDos exist
    Given the server is running
    And a ToDo with ID equal to 1 exists with title "Buy groceries", doneStatus false, and description "Milk, eggs, bread"
    And a ToDo with ID equal to 2 exists with title "Call mom", doneStatus false, and description "Weekly call"
  # Normal Flow

  Scenario Outline: Amending a ToDo with updated details
    Given a ToDo with ID equal to <id> exists
    When the user requests to update the ToDo with id <id> setting title to <title>, doneStatus to <doneStatus>, and description to <description>
    Then the ToDo with id <id> is updated with title <title>, doneStatus <doneStatus>, and description <description>
    And the user is notified of the completion of the update operation

    Examples:
      | id | title                      | doneStatus | description                     |
      |  1 | "Buy groceries and fruits" | false      | "Milk, eggs, bread, and apples" |
  # Alternate Flow

  Scenario Outline: Partially amending a ToDo with only some fields updated
    Given a ToDo with ID equal to <id> exists
    When the user requests to update the ToDo with id <id> setting only description to <description>
    Then the ToDo with id <id> retains its original title and doneStatus, and the description is updated to <description>
    And the user is notified of the completion of the update operation

    Examples:
      | id | description           |
      |  2 | "Weekly call updated" |
  # Error Flow

  Scenario Outline: Amending a ToDo with an invalid ID
    Given a ToDo with ID equal to <id> does not exist
    When the user requests to update the ToDo with id <id> setting title to <title>
    Then the user is notified of the non-existence error with a message <message>

    Examples:
      | id | title            | message                                                 |
      | 50 | "Invalid update" | "No such todo entity instance with GUID or ID 50 found" |
