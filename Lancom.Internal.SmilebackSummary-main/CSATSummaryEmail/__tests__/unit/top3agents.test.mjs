import { calculateIndividualCsatScores, calculateTopThreeAgents } from '../../src/dataProcessingHelpers.js';
import { jest } from '@jest/globals';

describe('Test is for topThreeAgent calculation', function () {
  it('Verifies sorting by score', async () => {
    console.info = jest.fn()

    var reviews = [
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 0
        },
        {
            "ticket": {
            "agents": [ "Agent2"],
            },
            "rating": -1
        },
        {
            "ticket": {
            "agents": ["Agent2"],
            },
            "rating": -1
        },
        {
            "ticket": {
            "agents": ["Agent2"],
            },
            "rating": -1
        }
    ]
    const top3 = calculateTopThreeAgents(reviews);

    expect (top3.length).toBe(2);
    expect (top3[0][0]).toBe("Agent1");
    expect (top3[1][0]).toBe("Agent2");
  });
  it ('verifies sorting with scores in reverse order', function () {
    console.info = jest.fn()

    var reviews = [
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": -1
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": -1
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 0
        },
        {
            "ticket": {
            "agents": [ "Agent2"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent2"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent2"],
            },
            "rating": 0
        }
    ]
    const scores = calculateIndividualCsatScores(reviews);
    console.log(scores);
    const top3 = calculateTopThreeAgents(reviews);
    console.log(top3);

    expect (top3.length).toBe(2);
    expect (top3[0][0]).toBe("Agent2");
    expect (top3[1][0]).toBe("Agent1");
  });
  it ('verifies sorting with same scores different number of reviews for agents', function () {
    console.info = jest.fn()

    var reviews = [
        {
            "ticket": {
            "agents": ["Agent1", "Agent2"],
            },
            "rating": 0
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 0
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 0
        },
        {
            "ticket": {
            "agents": [ "Agent2"],
            },
            "rating": 0
        },
        {
            "ticket": {
            "agents": ["Agent2"],
            },
            "rating": 0
        },
        {
            "ticket": {
            "agents": ["Agent2"],
            },
            "rating": 0
        }
    ]
    const scores = calculateIndividualCsatScores(reviews);
    const top3 = calculateTopThreeAgents(reviews);

    expect (top3.length).toBe(2);
    expect (top3[0][0]).toBe("Agent2");
    expect (top3[1][0]).toBe("Agent1");
  });
  it ('verifies sorting with different scores and different totals', function () {
    console.info = jest.fn()

    var reviews = [
        {
            "ticket": {
            "agents": ["Agent1", "Agent2"],
            },
            "rating": -1
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": -1
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 0
        },
        {
            "ticket": {
            "agents": [ "Agent2"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent2"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent2"],
            },
            "rating": 0
        }
    ]

    const top3 = calculateTopThreeAgents(reviews);

    expect (top3.length).toBe(2);
    expect (top3[0][0]).toBe("Agent2");
    expect (top3[1][0]).toBe("Agent1");
  });
  it ('verifies sorting with scores same and agent list in reverse order', function () {
    console.info = jest.fn()

    var reviews = [
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent1"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": [ "Agent2"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent2"],
            },
            "rating": 1
        },
        {
            "ticket": {
            "agents": ["Agent2", "Agent1"],
            },
            "rating": 1
        }
    ]
    const scores = calculateIndividualCsatScores(reviews);
    console.log(scores);
    const top3 = calculateTopThreeAgents(reviews);
    console.log(top3);

    expect (top3.length).toBe(2);
    expect (top3[0][0]).toBe("Agent1");
    expect (top3[1][0]).toBe("Agent2");
  });
});
