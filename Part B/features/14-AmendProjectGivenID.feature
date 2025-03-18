Feature: Amend a Project Given an ID
  As a user, I want to amend a specific Project to update its details.

  Background:
    Given the system contains the following projects
      | id | title                | completed | active | description                 |
      | 1  | "Website Redesign"   | false     | true   | "Update company website"    |
      | 2  | "Mobile App Dev"     | false     | true   | "Develop iOS/Android app"   |
      | 3  | "Year-end Reports"   | true      | false  | "Prepare financial reports" |

  # Normal Flow
  Scenario: Update all fields of a Project
    Given I have the following updated project information
      | title                  | completed | active | description                       |
      | "Website Modernization" | false     | true   | "Redesign with modern framework" |
    When I send a PUT request to "/projects/1" with this updated information
    Then the response status should be 200
    And the response should contain the updated project
    And the project with ID 1 should have all fields updated to the new values

  # Alternate Flow
  Scenario: Update only some fields of a Project
    Given I have the following partial project update
      | completed | description                       |
      | true      | "Website redesign completed"     |
    When I send a PUT request to "/projects/1" with this partial update
    Then the response status should be 200
    And the response should contain the updated project
    And the project with ID 1 should have the specified fields updated
    And the project with ID 1 should have unchanged values for other fields

  # Error Flow
  Scenario: Attempt to update a Project with an invalid ID
    Given I have valid project update information
    When I send a PUT request to "/projects/invalid-id" with this information
    Then the response status should be 400
    And the response should contain an error message about invalid ID format