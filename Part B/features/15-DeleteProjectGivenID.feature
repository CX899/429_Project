Feature: Delete a Project Given an ID
  As a user, I want to delete a specific Project to remove it.

  Background:
    Given the system contains the following projects
      | id | title                | completed | active | description                 |
      | 1  | "Website Redesign"   | false     | true   | "Update company website"    |
      | 2  | "Mobile App Dev"     | false     | true   | "Develop iOS/Android app"   |
      | 3  | "Year-end Reports"   | true      | false  | "Prepare financial reports" |

  # Normal Flow
  Scenario Outline: Delete a specific Project by ID
    When I send a <method> request to "/projects/<id>"
    Then the response status should be 200
    When the user sends a GET request to "/projects"
    Then the response should not contain a project with ID <id>
    And the response should contain projects with IDs <remaining_ids>

    Examples:
      | method | id | remaining_ids |
      | DELETE | 2  | 1 and 3       |

  # Alternate Flow
  Scenario Outline: Attempt to delete a Project with a valid but non-existent ID
    When I send a <method> request to "/projects/<id>"
    Then the response status should be 404
    And the response should contain a "Not Found" message

    Examples:
      | method | id  |
      | DELETE | 999 |

  # Error Flow
  Scenario Outline: Attempt to delete a Project with an invalid ID format
    When I send a <method> request to "/projects/<invalid_id>"
    Then the response status should be 404
    And the response JSON should contain an error message mentioning "Could not find any instances with projects/<invalid_id>"

    Examples:
      | method | invalid_id |
      | DELETE | invalid-id |