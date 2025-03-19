Feature: Amend a Project Given an ID
  As a user, I want to amend a specific Project to update its details.

  Background:
    Given the system contains the following projects
      | id | title                | completed | active | description                 |
      | 1  | "Website Redesign"   | false     | true   | "Update company website"    |
      | 2  | "Mobile App Dev"     | false     | true   | "Develop iOS/Android app"   |
      | 3  | "Year-end Reports"   | true      | false  | "Prepare financial reports" |

  # Normal Flow
  Scenario Outline: Update all fields of a Project
    Given I have the following updated project information
      | title       | completed   | active   | description       |
      | "<title>"   | <completed> | <active> | "<description>"   |
    When I send a <method> request to "/projects/<id>" with this updated information
    Then the response status should be 200
    And the response should contain the updated project
    And the project with ID <id> should have all fields updated to the new values

    Examples:
      | method | id | title                 | completed | active | description                     |
      | PUT    | 1  | Website Modernization | false     | true   | Redesign with modern framework |

  # Alternate Flow
  Scenario Outline: Update only some fields of a Project
    Given I have the following partial project update
      | completed   | description       |
      | <completed> | "<description>"   |
    When I send a PUT request to "/projects/<id>" with this partial update
    Then the response status should be 200
    And the response should contain the updated project
    And the project with ID <id> should have the specified fields updated
    And the project with ID <id> should have unchanged values for other fields

    Examples:
      | id | completed | description                   |
      | 1  | true      | Website redesign completed    |

  # Error Flow
  Scenario Outline: Attempt to update a Project with an invalid ID
    Given I have valid project update information
    When I send a <method> request to "/projects/<invalid_id>" with this information
    Then the response status should be 404
    And the response JSON should contain an error message mentioning "Invalid GUID for <invalid_id> entity project"

    Examples:
      | method | invalid_id |
      | PUT    | 999        |
      | PUT    | invalid-id |