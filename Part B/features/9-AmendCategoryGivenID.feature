Feature: Amend a Category Given an ID
  As a user, I want to amend a specific Category to update its details.

  Background:
    Given the system contains the following categories
      | id | title      | description          |
      | 1  | "Work"     | "Work related tasks" |
      | 2  | "Personal" | "Personal tasks"     |
      | 3  | "Shopping" | "Items to purchase"  |

  # Normal Flow
  Scenario Outline: Update a Category with complete new data
    Given I have the following updated category data
      | title         | description        |
      | "<new_title>" | "<new_description>" |
    When I send a <method> request to "/categories/<id>" with the updated data
    Then the response status should be 200
    And the response JSON should include the following updated category:
      | id   | title         | description        |
      | <id> | "<new_title>" | "<new_description>" |

    Examples:
      | id | method | new_title     | new_description         |
      | 1  | PUT    | Work Projects | Professional activities |

  # Alternate Flow
  Scenario Outline: Update only specific fields of a Category
    Given I have the following partial category data
      | <field_to_update>  |
      | "<updated_value>"  |
    When I send a <method> request to "/categories/<id>" with the partial data
    Then the response status should be 200
    And the response JSON should include the following updated category:
      | id   | title      | description      |
      | <id> | "<title>"  | "<description>"  |

    Examples:
      | id | method | field_to_update | updated_value  | title    | description    |
      | 2  | PUT    | description     | Daily routines | Personal | Daily routines |

  # Error Flow
  Scenario Outline: Update a Category with invalid ID
    Given I have the following updated category data
      | title      | description     |
      | "<title>"  | "<description>" |
    When I send a <method> request to "/categories/<invalid_id>" with the updated data
    Then the response status should be 400
    And the response should include an error message indicating invalid ID format

    Examples:
      | method | invalid_id | title   | description |
      | PUT    | abc        | Updated | New desc   |
