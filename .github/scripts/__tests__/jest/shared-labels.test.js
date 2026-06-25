// __tests__/jest/shared-labels.test.js
//
// Run from .github/scripts:
// npm run test:js -- shared-labels.test.js

function clearLabelEnv() {
  delete process.env.GOOD_FIRST_ISSUE_LABEL;
  delete process.env.GOOD_FIRST_ISSUE_CANDIDATE_LABEL;
  delete process.env.BEGINNER_LABEL;
  delete process.env.INTERMEDIATE_LABEL;
  delete process.env.ADVANCED_LABEL;
}

function freshRequire() {
  jest.resetModules();
  return require('../../shared/labels');
}

describe('labels.js — default exports', () => {
  let labels;

  beforeEach(() => {
    clearLabelEnv();
    labels = freshRequire();
  });

  afterEach(() => {
    clearLabelEnv();
  });

  test('exports correct default GOOD_FIRST_ISSUE_LABEL', () => {
    expect(labels.GOOD_FIRST_ISSUE_LABEL)
      .toBe('Good First Issue');
  });

  test('exports correct default GOOD_FIRST_ISSUE_CANDIDATE_LABEL', () => {
    expect(labels.GOOD_FIRST_ISSUE_CANDIDATE_LABEL)
      .toBe('Good First Issue Candidate');
  });

  test('exports correct default BEGINNER_LABEL', () => {
    expect(labels.BEGINNER_LABEL)
      .toBe('skill: beginner');
  });

  test('exports correct default INTERMEDIATE_LABEL', () => {
    expect(labels.INTERMEDIATE_LABEL)
      .toBe('skill: intermediate');
  });

  test('exports correct default ADVANCED_LABEL', () => {
    expect(labels.ADVANCED_LABEL)
      .toBe('skill: advanced');
  });

  test('exports DIFFICULTY_LABELS array with all four difficulty tiers', () => {
    expect(labels.DIFFICULTY_LABELS).toHaveLength(4);

    expect(labels.DIFFICULTY_LABELS)
      .toContain('Good First Issue');

    expect(labels.DIFFICULTY_LABELS)
      .toContain('skill: beginner');

    expect(labels.DIFFICULTY_LABELS)
      .toContain('skill: intermediate');

    expect(labels.DIFFICULTY_LABELS)
      .toContain('skill: advanced');
  });

  test('orders DIFFICULTY_LABELS by ascending difficulty', () => {
    expect(labels.DIFFICULTY_LABELS).toEqual([
      'Good First Issue',
      'skill: beginner',
      'skill: intermediate',
      'skill: advanced',
    ]);
  });

  test('does not include GOOD_FIRST_ISSUE_CANDIDATE_LABEL in DIFFICULTY_LABELS', () => {
    expect(labels.DIFFICULTY_LABELS)
      .not.toContain('Good First Issue Candidate');
  });
});

describe('labels.js — isSafeLabel', () => {
  let isSafeLabel;

  beforeEach(() => {
    clearLabelEnv();
    isSafeLabel = freshRequire().isSafeLabel;
  });

  afterEach(() => {
    clearLabelEnv();
  });

  test('accepts "Good First Issue"', () => {
    expect(isSafeLabel('Good First Issue')).toBe(true);
  });

  test('accepts "Good First Issue Candidate"', () => {
    expect(isSafeLabel('Good First Issue Candidate')).toBe(true);
  });

  test('accepts "skill: beginner"', () => {
    expect(isSafeLabel('skill: beginner')).toBe(true);
  });

  test('accepts "skill: intermediate"', () => {
    expect(isSafeLabel('skill: intermediate')).toBe(true);
  });

  test('accepts "skill: advanced"', () => {
    expect(isSafeLabel('skill: advanced')).toBe(true);
  });

  test('accepts simple alphanumeric labels', () => {
    expect(isSafeLabel('beginner')).toBe(true);
    expect(isSafeLabel('scope/CI')).toBe(true);
  });

  test('rejects empty string', () => {
    expect(isSafeLabel('')).toBe(false);
  });

  test('rejects whitespace-only string', () => {
    expect(isSafeLabel('   ')).toBe(false);
  });

  test('rejects string with semicolon', () => {
    expect(isSafeLabel('label; DROP TABLE')).toBe(false);
  });

  test('rejects string with double quotes', () => {
    expect(isSafeLabel('label"injection')).toBe(false);
  });

  test('rejects string with newline', () => {
    expect(isSafeLabel('label\ninjection')).toBe(false);
  });

  test('rejects non-string input', () => {
    expect(isSafeLabel(null)).toBe(false);
    expect(isSafeLabel(undefined)).toBe(false);
    expect(isSafeLabel(42)).toBe(false);
  });
});

describe('labels.js — environment variable overrides', () => {
  beforeEach(() => {
    clearLabelEnv();
  });

  afterEach(() => {
    clearLabelEnv();
  });

  test('overrides GOOD_FIRST_ISSUE_LABEL from env', () => {
    process.env.GOOD_FIRST_ISSUE_LABEL = 'custom: gfi';

    const labels = freshRequire();

    expect(labels.GOOD_FIRST_ISSUE_LABEL)
      .toBe('custom: gfi');

    expect(labels.DIFFICULTY_LABELS)
      .toContain('custom: gfi');
  });

  test('overrides GOOD_FIRST_ISSUE_CANDIDATE_LABEL from env', () => {
    process.env.GOOD_FIRST_ISSUE_CANDIDATE_LABEL =
      'custom: gfi candidate';

    const labels = freshRequire();

    expect(labels.GOOD_FIRST_ISSUE_CANDIDATE_LABEL)
      .toBe('custom: gfi candidate');
  });

  test('overrides BEGINNER_LABEL from env', () => {
    process.env.BEGINNER_LABEL = 'custom: beginner';

    const labels = freshRequire();

    expect(labels.BEGINNER_LABEL)
      .toBe('custom: beginner');

    expect(labels.DIFFICULTY_LABELS)
      .toContain('custom: beginner');
  });

  test('overrides INTERMEDIATE_LABEL from env', () => {
    process.env.INTERMEDIATE_LABEL = 'custom: intermediate';

    const labels = freshRequire();

    expect(labels.INTERMEDIATE_LABEL)
      .toBe('custom: intermediate');
  });

  test('overrides ADVANCED_LABEL from env', () => {
    process.env.ADVANCED_LABEL = 'custom: advanced';

    const labels = freshRequire();

    expect(labels.ADVANCED_LABEL)
      .toBe('custom: advanced');
  });

  test('trims whitespace from env values', () => {
    process.env.BEGINNER_LABEL = '  padded label  ';

    const labels = freshRequire();

    expect(labels.BEGINNER_LABEL)
      .toBe('padded label');
  });
});
