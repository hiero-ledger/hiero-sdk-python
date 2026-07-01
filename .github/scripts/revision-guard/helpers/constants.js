const DEFAULT_MANAGED_LABELS = [
  'queue:junior-committer',
  'queue:committers',
  'queue:maintainers',
  'status: ready-to-merge',
  'status: failed checks',
  'open to community review',
];

function parseManagedLabels(value) {
  if (typeof value !== 'string' || value.trim().length === 0) {
    return [...DEFAULT_MANAGED_LABELS];
  }

  const customLabels = value
    .split(',')
    .map(label => label.trim())
    .filter(Boolean);

  // Merge custom labels with defaults so that setting REVISION_GUARD_MANAGED_LABELS
  // adds to the managed set rather than silently discarding the default labels.
  const merged = new Set([...DEFAULT_MANAGED_LABELS, ...customLabels]);
  return [...merged];
}

module.exports = {
  DEFAULT_MANAGED_LABELS,
  parseManagedLabels,
};
