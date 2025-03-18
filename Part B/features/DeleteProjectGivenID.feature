Feature: Delete a Project Given an ID
  As a user, I want to delete a specific Project to remove it.

  Background:
    Given the system contains the following projects
      | id | title                | completed | active | description                 |
      | 1  | "Website Redesign"   | false     | true   | "Update company website"    |
      | 2  | "Mobile App Dev"     | false     | true   | "Develop iOS/Android app"   |
      | 3  | "Year-end Reports"   | true      | false  | "Prepare financial reports" |

  # Normal Flow
  Scenario: Delete a specific Project by ID
    When I send a DELETE request to "/projects/2"
    Then the response status should be 204
    And when I send a GET request to "/projects"
    Then the response should not contain a project with ID 2
    And the response should contain projects with IDs 1 and 3

  # Alternate Flow
  Scenario: Attempt to delete a Project with a valid but non-existent ID
    When I send a DELETE request to "/projects/999"
    Then the response status should be 404
    And the response should contain a "Not Found" message

  # Error Flow
  Scenario: Attempt to delete a Project with an invalid ID format
    When I send a DELETE request to "/projects/invalid-id"
    Then the response status should be 400
    And the response should contain an error message about invalid ID format