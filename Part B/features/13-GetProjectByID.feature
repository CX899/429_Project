Feature: Get a Project Given an ID
  As a user, I want to get a specific Project to view its details.

  Background:
    Given the system contains the following projects
      | id | title                | completed | active | description                 |
      | 1  | "Website Redesign"   | false     | true   | "Update company website"    |
      | 2  | "Mobile App Dev"     | false     | true   | "Develop iOS/Android app"   |
      | 3  | "Year-end Reports"   | true      | false  | "Prepare financial reports" |

  # Normal Flow
  Scenario Outline: Retrieve a specific Project by ID
    When I send a <method> request to "/projects/<id>"
    Then the response status should be 200
    And the response JSON should contain a project with the following details:
      | id   | title       | completed   | active   | description       |
      | <id> | "<title>"   | <completed> | <active> | "<description>"   |

    Examples:
      | method | id | title          | completed | active | description             |
      | GET    | 2  | Mobile App Dev | false     | true   | Develop iOS/Android app |

  # Alternate Flow
  Scenario Outline: Attempt to retrieve a Project with a valid but non-existent ID
    When I send a <method> request to "/projects/<id>"
    Then the response status should be 404
    And the response should contain a "Not Found" message

    Examples:
      | method | id  |
      | GET    | 999 |

  # Error Flow
  Scenario Outline: Attempt to retrieve a Project with an invalid ID format
    When I send a <method> request to "/projects/<invalid_id>"
    Then the response status should be 400
    And the response should contain an error message about invalid ID format

    Examples:
      | method | invalid_id  |
      | GET    | invalid-id  |
