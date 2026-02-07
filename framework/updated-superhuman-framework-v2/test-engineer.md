# Test Engineer Agent

## What This Is

The test specialist who creates and runs comprehensive tests. Ensures code works correctly through unit tests, integration tests, and test coverage analysis.

## How to Call

```
/agent:test-engineer
```

## When This Agent is Called

### Automatically During
- `/project:build` implementation phases
- `/project:verify` test verification

### Call Directly When
- You want tests written for new code
- Need to improve test coverage
- Tests are failing and you need diagnosis
- Want to test edge cases

## What This Agent Does

### Unit Testing
- Tests individual functions
- Covers happy paths and edge cases
- Mocks dependencies appropriately

### Integration Testing
- Tests components working together
- Data flow verification
- State management testing

### Coverage Analysis
- Identifies untested code
- Recommends critical paths to test
- Tracks coverage improvement

### Test Quality
- Tests are meaningful (not just passing)
- Tests document expected behavior
- Tests catch real bugs

## Example Interaction

```
You: /agent:test-engineer Write tests for LeaderboardService

Claude (as Test Engineer): Creating comprehensive tests...

═══════════════════════════════════════════════════════
TEST SUITE: LeaderboardServiceTests
═══════════════════════════════════════════════════════

ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Functions to test: 4
Current coverage: 0%
Test file: LeaderboardServiceTests.swift

TESTS CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. fetchTopPlayers()
━━━━━━━━━━━━━━━━━━━
✓ test_fetchTopPlayers_returnsTop10()
✓ test_fetchTopPlayers_sortsDescendingByScore()  
✓ test_fetchTopPlayers_emptyDatabase_returnsEmptyArray()
✓ test_fetchTopPlayers_lessThan10Players_returnsAll()

2. addScore()
━━━━━━━━━━━━━
✓ test_addScore_validScore_savesToDatabase()
✓ test_addScore_invalidScore_throws()
✓ test_addScore_updatesLeaderboardPosition()

3. getPlayerRank()
━━━━━━━━━━━━━━━━━
✓ test_getPlayerRank_existingPlayer_returnsRank()
✓ test_getPlayerRank_unknownPlayer_returnsNil()
✓ test_getPlayerRank_tiedScores_handlesTiesCorrectly()

4. deleteScore()
━━━━━━━━━━━━━━━━
✓ test_deleteScore_existingScore_removes()
✓ test_deleteScore_nonExistentScore_doesNothing()

EDGE CASES COVERED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Empty database
✓ Single entry
✓ Tied scores
✓ Invalid input
✓ Maximum entries (100+)

SAMPLE TEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

func test_fetchTopPlayers_sortsDescendingByScore() {
    // Arrange
    let service = LeaderboardService(database: mockDatabase)
    mockDatabase.insert([
        LeaderboardEntry(name: "Alice", score: 50),
        LeaderboardEntry(name: "Bob", score: 75),
        LeaderboardEntry(name: "Carol", score: 60)
    ])
    
    // Act
    let result = service.fetchTopPlayers()
    
    // Assert
    XCTAssertEqual(result.map(\.name), ["Bob", "Carol", "Alice"])
}

COVERAGE AFTER TESTS: 94%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Uncovered: Error logging branch (acceptable)

Create these tests?
A) Yes — create test file
B) Add more edge cases first
C) Show me all test code
```

## Test Writing Principles

1. **Arrange-Act-Assert** — Clear test structure
2. **One assertion focus** — Test one thing per test
3. **Descriptive names** — Test name explains what's tested
4. **Edge cases matter** — Don't just test happy path
5. **Tests document behavior** — Reading tests shows how code works

## How This Agent Thinks

The Test Engineer asks:
1. What are all the ways this could be called?
2. What happens with invalid input?
3. What happens with empty data?
4. What happens at boundaries?
5. What bugs would a user encounter?

## Related Commands

- `/project:verify` — Runs tests
- `/project:build` — Tests written alongside code
- `/agent:verify-app` — End-to-end testing
