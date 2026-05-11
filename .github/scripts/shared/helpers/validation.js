/**
 * Validates that a label string is safe to interpolate into
 * GitHub search queries.
 *
 * Rejects empty values and characters that could break or
 * alter query parsing semantics.
 *
 * @param {string} label
 * @returns {boolean}
 */
function isSafeLabel(label) {
  return typeof label === 'string'
    && label.length > 0
    && label.length <= 100
    && !/[\\"]/u.test(label);
}

module.exports = {
  isSafeLabel,
};
