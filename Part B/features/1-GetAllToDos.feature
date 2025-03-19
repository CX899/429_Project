Feature: Get All ToDos
  As a user, I want to get all ToDos so that I can view all of them and their amount.

  Background:
    Given the API contains todos data
  # Normal Flow

  Scenario Outline: Retrieve all ToDos with endpoint "<endpoint>"
    When the user sends a GET request to "<endpoint>"
    Then the response status should be 200
    And the response contains a list of todos

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

    Examples:
      | method | invalid_endpoint     | status |
      | PATCH  | /todos               |    405 |
      | GET    | /todoss              |    404 |
      | GET    | /todos?doneStatus=xx |    200 |