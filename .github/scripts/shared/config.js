// CONFIG helper

const {
  GOOD_FIRST_ISSUE_LABEL,
  BEGINNER_LABEL,
  INTERMEDIATE_LABEL,
  ADVANCED_LABEL,
} = require('./labels');

const { isSafeLabel } = require('./helpers/validation');

/**
 * Validates configured repository label strings.
 *
 * Labels are interpolated into GitHub search queries, so invalid or unsafe
 * values should fail fast during module initialization.
 *
 * @param {Array<object>} repos
 */

function validateRepoLabels(repos) {
  for (const repo of repos) {
    for (const [level, label] of Object.entries(repo.labels ?? {})) {
      if (!isSafeLabel(label)) {
        throw new Error(
          `Unsafe label configured for ${repo.owner}/${repo.repo} (${level}): "${label}"`
        );
      }
    }
  }
}
const LEVEL_KEYS = {
  GFI: 'gfi',
  BEGINNER: 'beginner',
  INTERMEDIATE: 'intermediate',
  ADVANCED: 'advanced',
};

const CONFIG = {
  // Internal canonical keys — never used as label strings directly.
  // GFI is index 0 and is entry-only: never recommended after first completion.
  skillHierarchy: [
  LEVEL_KEYS.GFI,
  LEVEL_KEYS.BEGINNER,
  LEVEL_KEYS.INTERMEDIATE,
  LEVEL_KEYS.ADVANCED,
  ],

  // requiredLevel: canonical key the contributor must have completed N times
  // requiredCount: completions needed (0 = no prerequisite)
  skillPrerequisites: {
    [LEVEL_KEYS.GFI]:          { requiredLevel: null,           requiredCount: 0, displayName: 'Good First Issue' },
    [LEVEL_KEYS.BEGINNER]:     { requiredLevel: 'LEVEL_KEYS.GFI',          requiredCount: 1, displayName: 'Beginner'         },
    [LEVEL_KEYS.INTERMEDIATE]: { requiredLevel: 'LEVEL_KEYS.BEGINNER',     requiredCount: 3, displayName: 'Intermediate'     },
    [LEVEL_KEYS.ADVANCED]:     { requiredLevel: 'LEVEL_KEYS.INTERMEDIATE', requiredCount: 3, displayName: 'Advanced'         },
  },

  // Repos tried in order for each fallback step.
  // Home repo must be first — contributor history is resolved against it.
  repos: [
    {
      owner: 'hiero-ledger',
      repo:  'hiero-sdk-python',
      isHome: true,
      repositoryUrl: 'https://github.com/hiero-ledger/hiero-sdk-python',
        communityLinks: {
          discord: 'https://discord.com/invite/hyperledger',
        },
      botSignature: 'Hiero Python SDK Team',
      labels: {
        gfi:          GOOD_FIRST_ISSUE_LABEL,
        beginner:     BEGINNER_LABEL,
        intermediate: INTERMEDIATE_LABEL,
        advanced:     ADVANCED_LABEL,
      },
    },
    {
      owner: 'hiero-ledger',
      repo:  'hiero-sdk-cpp',
      labels: {
        gfi:          'skill: good first issue',
        beginner:     'skill: beginner',
        intermediate: 'skill: intermediate',
        advanced:     'skill: advanced',
      },
    },
  ],

  maxRecommendations: 5,
  fetchPerPage:       50,
  commentMarker:      '<!-- hiero-next-issue-bot -->',
};

validateRepoLabels(CONFIG.repos);

module.exports = {
  CONFIG,
  LEVEL_KEYS,
};
