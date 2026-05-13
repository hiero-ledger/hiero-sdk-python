// node --test .github/scripts/tests/recommendation.test.js

const assert = require('node:assert/strict');
const test = require('node:test');

const {
  computeLevelStepIndices,
  buildFallbackChain,
} = require('../shared/core/recommendation');

const {
  adjustEligibilityForCurrentPR,
} = require('../shared/core/eligibility');

const { CONFIG } = require('../shared/config');

// ---------------------------------------------------------------------------
// computeLevelStepIndices
// ---------------------------------------------------------------------------

test('computeLevelStepIndices prefers level up, same, then level down', () => {
  const result = computeLevelStepIndices('beginner', 'intermediate');

  // beginner=1, intermediate=2
  assert.deepEqual(result, [2, 1]);
});

test('computeLevelStepIndices falls back to same and lower level', () => {
  const result = computeLevelStepIndices('intermediate', 'intermediate');

  // intermediate=2, beginner=1
  assert.deepEqual(result, [2, 1]);
});

test('computeLevelStepIndices never recommends gfi as fallback', () => {
  const result = computeLevelStepIndices('beginner', 'beginner');

  // beginner only (no gfi fallback)
  assert.deepEqual(result, [1]);
});

// ---------------------------------------------------------------------------
// buildFallbackChain
// ---------------------------------------------------------------------------

test('buildFallbackChain expands levels across repos in priority order', () => {
  const chain = buildFallbackChain('beginner', 'intermediate');

  assert.ok(chain.length > 0);

  // First recommendation should be intermediate in home repo
  assert.equal(chain[0].levelKey, 'intermediate');
  assert.equal(chain[0].repoConfig.isHome, true);

  // Level transitions should follow level-up -> same -> level-down ordering
  // (without gfi). Collect distinct levels in chain order.
  const distinctLevels = chain
    .map(e => e.levelKey)
    .filter((lvl, i, arr) => i === 0 || arr[i - 1] !== lvl);
  assert.deepEqual(distinctLevels, ['intermediate', 'beginner']);

  // Ensure no gfi recommendations exist
  const hasGfi = chain.some(entry => entry.levelKey === 'gfi');
  assert.equal(hasGfi, false);
});

// ---------------------------------------------------------------------------
// adjustEligibilityForCurrentPR
// ---------------------------------------------------------------------------

test('adjustEligibilityForCurrentPR bumps eligibility after completing current level', () => {
  const adjusted = adjustEligibilityForCurrentPR('gfi', 'gfi');

  assert.equal(adjusted, 'beginner');
});

test('adjustEligibilityForCurrentPR does not downgrade higher eligibility', () => {
  const adjusted = adjustEligibilityForCurrentPR(
    'beginner',
    'advanced',
  );

  assert.equal(adjusted, 'advanced');
});

// ---------------------------------------------------------------------------
// basic integration-style recommendation flow
// ---------------------------------------------------------------------------

test('fallback chain includes repos for eligible levels only', () => {
  const chain = buildFallbackChain('intermediate', 'advanced');

  assert.ok(chain.length > 0, 'expected non-empty fallback chain');

  const validLevels = new Set(CONFIG.skillHierarchy);

  for (const entry of chain) {
    assert.ok(validLevels.has(entry.levelKey));
    assert.ok(entry.repoConfig.owner);
    assert.ok(entry.repoConfig.repo);
  }
});
