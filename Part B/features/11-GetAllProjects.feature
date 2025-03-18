Feature: Get All Projects
  As a user, I want to get all Projects so that I can view them.

  Background:
    Given the system contains the following projects
      | id | title                | completed | active | description                 |
      | 1  | "Website Redesign"   | false     | true   | "Update company website"    |
      | 2  | "Mobile App Dev"     | false     | true   | "Develop iOS/Android app"   |
      | 3  | "Year-end Reports"   | true      | false  | "Prepare financial reports" |

  # Normal Flow
  Scenario Outline: Retrieve all Projects
    When I send a <method> request to "<endpoint>"
    Then the response status should be 200
    And the response JSON should include the following projects:
      | id | title                | completed | active | description                 |
      | 1  | "Website Redesign"   | false     | true   | "Update company website"    |
      | 2  | "Mobile App Dev"     | false     | true   | "Develop iOS/Android app"   |
      | 3  | "Year-end Reports"   | true      | false  | "Prepare financial reports" |

    Examples:
      | method | endpoint  |
      | GET    | /projects |

  # Alternate Flow
  Scenario Outline: Retrieve filtered Projects
    Given a filter where "<filter_key>" equals "<filter_value>"
    When I send a GET request to "/projects?<filter_key>=<filter_value>"
    Then the response status should be 200
    And the response JSON should contain only projects where <filter_key> equals "<filter_value>"
    
    Examples:
      | filter_key | filter_value       |
      | active     | true               |
      | completed  | true               |
      | title      | "Website Redesign" |

  # Error Flow
  Scenario Outline: Attempt to use unsupported HTTP method
    When I send a <method> request to "<endpoint>"
    Then the response status should be 405
    And the response should contain an error message

    Examples:
      | method | endpoint  |
      | PATCH  | /projects |
