// __tests__/jest/shared-review-stages.test.js
//
// Run from .github/scripts:
// npm run test:js -- shared-review-stages.test.js

const REVIEW_STAGE_ENV_KEYS = [
  'STAGE_AWAITING_REVIEW',
  'STAGE_CHANGES_REQUESTED',
  'STAGE_APPROVED',
  'STAGE_AWAITING_TRIAGE',
  'REVIEWER_TYPE_TRIAGE',
  'REVIEWER_TYPE_COMMITTER',
  'REVIEWER_TYPE_MAINTAINER',
];

const LABEL_ENV_KEYS = [
  'GOOD_FIRST_ISSUE_LABEL',
  'GOOD_FIRST_ISSUE_CANDIDATE_LABEL',
  'BEGINNER_LABEL',
  'INTERMEDIATE_LABEL',
  'ADVANCED_LABEL',
];

const ALL_ENV_KEYS = [...REVIEW_STAGE_ENV_KEYS, ...LABEL_ENV_KEYS];

// Snapshot whatever the environment actually had (which may be nothing, or
// may be real values set by the CI runner / a preceding test file sharing
// the same Jest worker) so it can be restored exactly, rather than always
// deleting the keys and leaving process.env permanently stripped of values
// that existed before this file ran.
function snapshotEnv(keys) {
  const snapshot = {};
  for (const key of keys) {
    snapshot[key] = process.env[key];
  }
  return snapshot;
}

function restoreEnv(snapshot) {
  for (const [key, value] of Object.entries(snapshot)) {
    if (value === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = value;
    }
  }
}

function clearEnv(keys) {
  for (const key of keys) {
    delete process.env[key];
  }
}

function freshRequire() {
  jest.resetModules();
  return require('../../shared/review-stages');
}

// For tests that pass label names in: pull the label values from the same
// config module the production code uses (shared/labels.js) rather than
// hardcoding the strings, so a renamed default label can't silently
// desynchronize these tests from getExpectedReviewers' actual behavior.
function freshRequireWithLabels() {
  jest.resetModules();
  return {
    stages: require('../../shared/review-stages'),
    labels: require('../../shared/labels'),
  };
}

describe('review-stages.js — stage constants', () => {
  let stages;
  let envSnapshot;

  beforeEach(() => {
    envSnapshot = snapshotEnv(ALL_ENV_KEYS);
    clearEnv(ALL_ENV_KEYS);
    stages = freshRequire();
  });

  afterEach(() => {
    restoreEnv(envSnapshot);
  });

  test('exports all four stage constants, non-empty', () => {
    expect(stages.AWAITING_REVIEW).toBeTruthy();
    expect(stages.CHANGES_REQUESTED).toBeTruthy();
    expect(stages.APPROVED).toBeTruthy();
    expect(stages.AWAITING_TRIAGE).toBeTruthy();
  });

  test('exports correct default stage values', () => {
    expect(stages.AWAITING_REVIEW).toBe('awaiting_review');
    expect(stages.CHANGES_REQUESTED).toBe('changes_requested');
    expect(stages.APPROVED).toBe('approved');
    expect(stages.AWAITING_TRIAGE).toBe('awaiting_triage');
  });

  test('exports REVIEW_STAGES array containing all five stages', () => {
    expect(stages.REVIEW_STAGES).toHaveLength(5);
    expect(stages.REVIEW_STAGES).toContain(stages.AWAITING_REVIEW);
    expect(stages.REVIEW_STAGES).toContain(stages.CHANGES_REQUESTED);
    expect(stages.REVIEW_STAGES).toContain(stages.APPROVED);
    expect(stages.REVIEW_STAGES).toContain(stages.AWAITING_TRIAGE);
    expect(stages.REVIEW_STAGES).toContain(stages.ROSTER_UNAVAILABLE);
  });
});

describe('review-stages.js — reviewer type constants', () => {
  let stages;
  let envSnapshot;

  beforeEach(() => {
    envSnapshot = snapshotEnv(ALL_ENV_KEYS);
    clearEnv(ALL_ENV_KEYS);
    stages = freshRequire();
  });

  afterEach(() => {
    restoreEnv(envSnapshot);
  });

  test('exports all three reviewer-type constants, non-empty', () => {
    expect(stages.TRIAGE).toBeTruthy();
    expect(stages.COMMITTER).toBeTruthy();
    expect(stages.MAINTAINER).toBeTruthy();
  });

  test('exports correct default reviewer-type values', () => {
    expect(stages.TRIAGE).toBe('triage');
    expect(stages.COMMITTER).toBe('committer');
    expect(stages.MAINTAINER).toBe('maintainer');
  });
});

describe('review-stages.js — getExpectedReviewers', () => {
  let stages;
  let labels;
  let envSnapshot;

  beforeEach(() => {
    envSnapshot = snapshotEnv(ALL_ENV_KEYS);
    clearEnv(ALL_ENV_KEYS);
    ({ stages, labels } = freshRequireWithLabels());
  });

  afterEach(() => {
    restoreEnv(envSnapshot);
  });

  test('GFI label maps to [TRIAGE, COMMITTER]', () => {
    expect(stages.getExpectedReviewers([labels.GOOD_FIRST_ISSUE_LABEL]))
      .toEqual([stages.TRIAGE, stages.COMMITTER]);
  });

  test('beginner label maps to [TRIAGE, COMMITTER]', () => {
    expect(stages.getExpectedReviewers([labels.BEGINNER_LABEL]))
      .toEqual([stages.TRIAGE, stages.COMMITTER]);
  });

  test('intermediate label maps to [COMMITTER, MAINTAINER]', () => {
    expect(stages.getExpectedReviewers([labels.INTERMEDIATE_LABEL]))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });

  test('advanced label maps to [COMMITTER, MAINTAINER]', () => {
    expect(stages.getExpectedReviewers([labels.ADVANCED_LABEL]))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });

  test('PR with no skill labels defaults to [COMMITTER, MAINTAINER]', () => {
    expect(stages.getExpectedReviewers([]))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });

  test('PR with unrelated non-skill labels defaults to [COMMITTER, MAINTAINER]', () => {
    expect(stages.getExpectedReviewers(['bug', 'documentation']))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });

  test('PR with both beginner and advanced labels uses the higher difficulty', () => {
    expect(stages.getExpectedReviewers([labels.BEGINNER_LABEL, labels.ADVANCED_LABEL]))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });

  test('PR with both GFI and intermediate labels uses the higher difficulty', () => {
    expect(stages.getExpectedReviewers([labels.GOOD_FIRST_ISSUE_LABEL, labels.INTERMEDIATE_LABEL]))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });

  test('handles undefined labels gracefully', () => {
    expect(stages.getExpectedReviewers(undefined))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });
});

describe('review-stages.js — environment variable overrides', () => {
  let envSnapshot;

  beforeEach(() => {
    envSnapshot = snapshotEnv(ALL_ENV_KEYS);
    clearEnv(ALL_ENV_KEYS);
  });

  afterEach(() => {
    restoreEnv(envSnapshot);
  });

  test('overrides AWAITING_REVIEW from env', () => {
    process.env.STAGE_AWAITING_REVIEW = 'custom: awaiting review';

    const stages = freshRequire();

    expect(stages.AWAITING_REVIEW).toBe('custom: awaiting review');
    expect(stages.REVIEW_STAGES).toContain('custom: awaiting review');
  });

  test('overrides TRIAGE reviewer type from env', () => {
    process.env.REVIEWER_TYPE_TRIAGE = 'custom-triage';

    const { stages, labels } = freshRequireWithLabels();

    expect(stages.TRIAGE).toBe('custom-triage');
    expect(stages.getExpectedReviewers([labels.GOOD_FIRST_ISSUE_LABEL]))
      .toContain('custom-triage');
  });

  test('trims whitespace from env values', () => {
    process.env.STAGE_APPROVED = '  padded stage  ';

    const stages = freshRequire();

    expect(stages.APPROVED).toBe('padded stage');
  });
});
