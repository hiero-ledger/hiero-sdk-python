// __tests__/jest/shared-review-stages.test.js
//
// Run from .github/scripts:
// npm run test:js -- shared-review-stages.test.js

function clearReviewStageEnv() {
  delete process.env.STAGE_AWAITING_REVIEW;
  delete process.env.STAGE_CHANGES_REQUESTED;
  delete process.env.STAGE_APPROVED;
  delete process.env.STAGE_AWAITING_TRIAGE;
  delete process.env.REVIEWER_TYPE_TRIAGE;
  delete process.env.REVIEWER_TYPE_COMMITTER;
  delete process.env.REVIEWER_TYPE_MAINTAINER;
}

function clearLabelEnv() {
  delete process.env.GOOD_FIRST_ISSUE_LABEL;
  delete process.env.GOOD_FIRST_ISSUE_CANDIDATE_LABEL;
  delete process.env.BEGINNER_LABEL;
  delete process.env.INTERMEDIATE_LABEL;
  delete process.env.ADVANCED_LABEL;
}

function freshRequire() {
  jest.resetModules();
  return require('../../shared/review-stages');
}

describe('review-stages.js — stage constants', () => {
  let stages;

  beforeEach(() => {
    clearReviewStageEnv();
    clearLabelEnv();
    stages = freshRequire();
  });

  afterEach(() => {
    clearReviewStageEnv();
    clearLabelEnv();
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

  test('exports REVIEW_STAGES array containing all four stages', () => {
    expect(stages.REVIEW_STAGES).toHaveLength(4);
    expect(stages.REVIEW_STAGES).toContain(stages.AWAITING_REVIEW);
    expect(stages.REVIEW_STAGES).toContain(stages.CHANGES_REQUESTED);
    expect(stages.REVIEW_STAGES).toContain(stages.APPROVED);
    expect(stages.REVIEW_STAGES).toContain(stages.AWAITING_TRIAGE);
  });
});

describe('review-stages.js — reviewer type constants', () => {
  let stages;

  beforeEach(() => {
    clearReviewStageEnv();
    clearLabelEnv();
    stages = freshRequire();
  });

  afterEach(() => {
    clearReviewStageEnv();
    clearLabelEnv();
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

  beforeEach(() => {
    clearReviewStageEnv();
    clearLabelEnv();
    stages = freshRequire();
  });

  afterEach(() => {
    clearReviewStageEnv();
    clearLabelEnv();
  });

  test('GFI label maps to [TRIAGE, COMMITTER]', () => {
    expect(stages.getExpectedReviewers(['Good First Issue']))
      .toEqual([stages.TRIAGE, stages.COMMITTER]);
  });

  test('beginner label maps to [TRIAGE, COMMITTER]', () => {
    expect(stages.getExpectedReviewers(['skill: beginner']))
      .toEqual([stages.TRIAGE, stages.COMMITTER]);
  });

  test('intermediate label maps to [COMMITTER, MAINTAINER]', () => {
    expect(stages.getExpectedReviewers(['skill: intermediate']))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });

  test('advanced label maps to [COMMITTER, MAINTAINER]', () => {
    expect(stages.getExpectedReviewers(['skill: advanced']))
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
    expect(stages.getExpectedReviewers(['skill: beginner', 'skill: advanced']))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });

  test('PR with both GFI and intermediate labels uses the higher difficulty', () => {
    expect(stages.getExpectedReviewers(['Good First Issue', 'skill: intermediate']))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });

  test('handles undefined labels gracefully', () => {
    expect(stages.getExpectedReviewers(undefined))
      .toEqual([stages.COMMITTER, stages.MAINTAINER]);
  });
});

describe('review-stages.js — environment variable overrides', () => {
  beforeEach(() => {
    clearReviewStageEnv();
    clearLabelEnv();
  });

  afterEach(() => {
    clearReviewStageEnv();
    clearLabelEnv();
  });

  test('overrides AWAITING_REVIEW from env', () => {
    process.env.STAGE_AWAITING_REVIEW = 'custom: awaiting review';

    const stages = freshRequire();

    expect(stages.AWAITING_REVIEW).toBe('custom: awaiting review');
    expect(stages.REVIEW_STAGES).toContain('custom: awaiting review');
  });

  test('overrides TRIAGE reviewer type from env', () => {
    process.env.REVIEWER_TYPE_TRIAGE = 'custom-triage';

    const stages = freshRequire();

    expect(stages.TRIAGE).toBe('custom-triage');
    expect(stages.getExpectedReviewers(['Good First Issue']))
      .toContain('custom-triage');
  });

  test('trims whitespace from env values', () => {
    process.env.STAGE_APPROVED = '  padded stage  ';

    const stages = freshRequire();

    expect(stages.APPROVED).toBe('padded stage');
  });
});
