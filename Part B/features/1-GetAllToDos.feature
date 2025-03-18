Feature: Get All ToDos
  As a user, I want to get all ToDos so that I can view all of them and their amount.

  Background:
    Given the system contains the following todos
      | id | title               | doneStatus | description         |
      |  1 | "Buy groceries"     | false      | "Milk, eggs, bread" |
      |  2 | "Call mom"          | false      | "Weekly call"       |
      |  3 | "Finish assignment" | false      | "Due tomorrow"      |
  # Normal Flow

  Scenario Outline: Retrieve all ToDos with endpoint "<endpoint>"
    When the user sends a GET request to "<endpoint>"
    Then the response status should be 200
    And the response JSON should include the following todos:
      | id | title               | doneStatus | description         |
      |  1 | "Buy groceries"     | false      | "Milk, eggs, bread" |
      |  2 | "Call mom"          | false      | "Weekly call"       |
      |  3 | "Finish assignment" | false      | "Due tomorrow"      |

    Examples:
      | endpoint |
      | /todos   |
  # Alternate Flow

  Scenario Outline: Retrieve filtered ToDos
    Given a filter where "<filter_key>" equals "<filter_value>"
    When the user sends a GET request to "/todos?<filter_key>=<filter_value>"
    Then the response status should be 200
    And the response JSON should contain only todos where <filter_key> equals "<filter_value>"

    Examples:
      | filter_key | filter_value    |
      | doneStatus | false           |
      | title      | "Buy groceries" |
  # Error Flow

  Scenario Outline: Request ToDos with unsupported or invalid request
    When the user sends a <method> request to "<invalid_endpoint>"
    Then the response status should be <status>
    And the response JSON should include an error message "<message>"

    Examples:
      | method | invalid_endpoint     | status | message                              |
      | PATCH  | /todos               |    405 | "Method Not Allowed"                 |
      | GET    | /todoss              |    404 | "Not Found"                          |
      | GET    | /todos?doneStatus=xx |    400 | "Invalid value for doneStatus field" |
