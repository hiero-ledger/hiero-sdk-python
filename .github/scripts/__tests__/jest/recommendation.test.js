// __tests__/jest/recommendation.test.js
//
// Run from .github/scripts:
// npm run test:js -- recommendation.test.js

const {
  computeLevelStepIndices,
  buildFallbackChain,
} = require('../../shared/core/recommendation');

const {
  adjustEligibilityForCurrentPR,
} = require('../../shared/core/eligibility');

const { CONFIG } = require('../../shared/config');

// ---------------------------------------------------------------------------
// computeLevelStepIndices
// ---------------------------------------------------------------------------
describe('computeLevelStepIndices', () => {
  test('prefers level up, same, then level down', () => {
    const result = computeLevelStepIndices('beginner', 'intermediate');

    // beginner = 1, intermediate = 2
    expect(result).toEqual([2, 1]);
  });

  test('falls back to same and lower level', () => {
    const result = computeLevelStepIndices('intermediate', 'intermediate');

    // intermediate = 2, beginner = 1
    expect(result).toEqual([2, 1]);
  });

  test('never recommends gfi as fallback', () => {
    const result = computeLevelStepIndices('beginner', 'beginner');

    // beginner only (no gfi fallback)
    expect(result).toEqual([1]);
  });
});

// ---------------------------------------------------------------------------
// buildFallbackChain
// ---------------------------------------------------------------------------
describe('buildFallbackChain', () => {
  test('expands levels across repos in priority order', () => {
    const chain = buildFallbackChain('beginner', 'intermediate');

    expect(chain.length).toBeGreaterThan(0);

    // First recommendation should be intermediate in home repo
    expect(chain[0].levelKey).toBe('intermediate');
    expect(chain[0].repoConfig.isHome).toBe(true);

    const distinctLevels = chain
      .map((e) => e.levelKey)
      .filter((lvl, i, arr) => i === 0 || arr[i - 1] !== lvl);

    // Level transitions should follow level-up -> same -> level-down ordering
    // (without gfi). Collect distinct levels in chain order.
    expect(distinctLevels).toEqual([
      'intermediate',
      'beginner',
    ]);

    // Ensure no gfi recommendations exist
    const hasGfi = chain.some(
      (entry) => entry.levelKey === 'gfi'
    );

    expect(hasGfi).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// adjustEligibilityForCurrentPR
// ---------------------------------------------------------------------------
describe('adjustEligibilityForCurrentPR', () => {
  test('bumps eligibility after completing current level', () => {
    const adjusted = adjustEligibilityForCurrentPR(
      'gfi',
      'gfi'
    );

    expect(adjusted).toBe('beginner');
  });

  test('does not downgrade higher eligibility', () => {
    const adjusted = adjustEligibilityForCurrentPR(
      'beginner',
      'advanced'
    );

    expect(adjusted).toBe('advanced');
  });
});

// ---------------------------------------------------------------------------
// basic integration-style recommendation flow
// ---------------------------------------------------------------------------
describe('recommendation integration', () => {
  test('fallback chain includes repos for eligible levels only', () => {
    const chain = buildFallbackChain(
      'intermediate',
      'advanced'
    );

    expect(chain.length).toBeGreaterThan(0);

    const validLevels = new Set(CONFIG.skillHierarchy);

    for (const entry of chain) {
      expect(validLevels.has(entry.levelKey)).toBe(true);
      expect(entry.repoConfig.owner).toBeDefined();
      expect(entry.repoConfig.repo).toBeDefined();
    }
  });
});
