/**
 * Unit tests for the shared labels module.
 *
 * Run with: node --test .github/scripts/shared/labels.test.js
 * Requires Node >= 18 (built-in test runner, no framework dependencies).
 */

const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');

function clearLabelEnv() {
  delete process.env.GOOD_FIRST_ISSUE_LABEL;
  delete process.env.GOOD_FIRST_ISSUE_CANDIDATE_LABEL;
  delete process.env.BEGINNER_LABEL;
  delete process.env.INTERMEDIATE_LABEL;
  delete process.env.ADVANCED_LABEL;
}

// Helper: force a fresh require() by clearing the module cache.
// labels.js reads process.env at load time, so we must reload to test overrides.
function freshRequire() {
  const modulePath = require.resolve('./labels.js');
  delete require.cache[modulePath];
  return require('./labels.js');
}

describe('labels.js — default exports', () => {
  let labels;

  beforeEach(() => {
    clearLabelEnv();
    labels = freshRequire();
  });

  afterEach(clearLabelEnv);

  it('exports correct default GOOD_FIRST_ISSUE_LABEL', () => {
    assert.equal(labels.GOOD_FIRST_ISSUE_LABEL, 'Good First Issue');
  });

  it('exports correct default GOOD_FIRST_ISSUE_CANDIDATE_LABEL', () => {
    assert.equal(labels.GOOD_FIRST_ISSUE_CANDIDATE_LABEL, 'Good First Issue Candidate');
  });

  it('exports correct default BEGINNER_LABEL', () => {
    assert.equal(labels.BEGINNER_LABEL, 'skill: beginner');
  });

  it('exports correct default INTERMEDIATE_LABEL', () => {
    assert.equal(labels.INTERMEDIATE_LABEL, 'skill: intermediate');
  });

  it('exports correct default ADVANCED_LABEL', () => {
    assert.equal(labels.ADVANCED_LABEL, 'skill: advanced');
  });

  it('exports DIFFICULTY_LABELS array with all four difficulty tiers', () => {
    assert.equal(labels.DIFFICULTY_LABELS.length, 4);
    assert.ok(labels.DIFFICULTY_LABELS.includes('Good First Issue'));
    assert.ok(labels.DIFFICULTY_LABELS.includes('skill: beginner'));
    assert.ok(labels.DIFFICULTY_LABELS.includes('skill: intermediate'));
    assert.ok(labels.DIFFICULTY_LABELS.includes('skill: advanced'));
  });

  it('orders DIFFICULTY_LABELS by ascending difficulty', () => {
    assert.deepEqual(labels.DIFFICULTY_LABELS, [
      'Good First Issue',
      'skill: beginner',
      'skill: intermediate',
      'skill: advanced',
    ]);
  });

  it('does not include GOOD_FIRST_ISSUE_CANDIDATE_LABEL in DIFFICULTY_LABELS', () => {
    assert.ok(!labels.DIFFICULTY_LABELS.includes('Good First Issue Candidate'));
  });
});

describe('labels.js — isSafeLabel', () => {
  let isSafeLabel;

  beforeEach(() => {
    clearLabelEnv();
    isSafeLabel = freshRequire().isSafeLabel;
  });

  afterEach(clearLabelEnv);

  it('accepts "Good First Issue"', () => {
    assert.ok(isSafeLabel('Good First Issue'));
  });

  it('accepts "Good First Issue Candidate"', () => {
    assert.ok(isSafeLabel('Good First Issue Candidate'));
  });

  it('accepts "skill: beginner"', () => {
    assert.ok(isSafeLabel('skill: beginner'));
  });

  it('accepts "skill: intermediate"', () => {
    assert.ok(isSafeLabel('skill: intermediate'));
  });

  it('accepts "skill: advanced"', () => {
    assert.ok(isSafeLabel('skill: advanced'));
  });

  it('accepts simple alphanumeric labels', () => {
    assert.ok(isSafeLabel('beginner'));
    assert.ok(isSafeLabel('scope/CI'));
  });

  it('rejects empty string', () => {
    assert.equal(isSafeLabel(''), false);
  });

  it('rejects whitespace-only string', () => {
    assert.equal(isSafeLabel('   '), false);
  });

  it('rejects string with semicolon (injection)', () => {
    assert.equal(isSafeLabel('label; DROP TABLE'), false);
  });

  it('rejects string with double quotes', () => {
    assert.equal(isSafeLabel('label"injection'), false);
  });

  it('rejects string with newline', () => {
    assert.equal(isSafeLabel('label\ninjection'), false);
  });

  it('rejects non-string input', () => {
    assert.equal(isSafeLabel(null), false);
    assert.equal(isSafeLabel(undefined), false);
    assert.equal(isSafeLabel(42), false);
  });
});

describe('labels.js — environment variable overrides', () => {
  beforeEach(clearLabelEnv);
  afterEach(clearLabelEnv);

  it('overrides GOOD_FIRST_ISSUE_LABEL from env', () => {
    process.env.GOOD_FIRST_ISSUE_LABEL = 'custom: gfi';
    const labels = freshRequire();
    assert.equal(labels.GOOD_FIRST_ISSUE_LABEL, 'custom: gfi');
    assert.ok(labels.DIFFICULTY_LABELS.includes('custom: gfi'));
  });

  it('overrides GOOD_FIRST_ISSUE_CANDIDATE_LABEL from env', () => {
    process.env.GOOD_FIRST_ISSUE_CANDIDATE_LABEL = 'custom: gfi candidate';
    const labels = freshRequire();
    assert.equal(labels.GOOD_FIRST_ISSUE_CANDIDATE_LABEL, 'custom: gfi candidate');
  });

  it('overrides BEGINNER_LABEL from env', () => {
    process.env.BEGINNER_LABEL = 'custom: beginner';
    const labels = freshRequire();
    assert.equal(labels.BEGINNER_LABEL, 'custom: beginner');
    assert.ok(labels.DIFFICULTY_LABELS.includes('custom: beginner'));
  });

  it('overrides INTERMEDIATE_LABEL from env', () => {
    process.env.INTERMEDIATE_LABEL = 'custom: intermediate';
    const labels = freshRequire();
    assert.equal(labels.INTERMEDIATE_LABEL, 'custom: intermediate');
  });

  it('overrides ADVANCED_LABEL from env', () => {
    process.env.ADVANCED_LABEL = 'custom: advanced';
    const labels = freshRequire();
    assert.equal(labels.ADVANCED_LABEL, 'custom: advanced');
  });

  it('trims whitespace from env values', () => {
    process.env.BEGINNER_LABEL = '  padded label  ';
    const labels = freshRequire();
    assert.equal(labels.BEGINNER_LABEL, 'padded label');
  });
});
