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

  return value
    .split(',')
    .map(label => label.trim())
    .filter(Boolean);
}

module.exports = {
  DEFAULT_MANAGED_LABELS,
  parseManagedLabels,
};
