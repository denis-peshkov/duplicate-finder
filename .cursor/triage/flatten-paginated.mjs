/**
 * Flatten `gh api --paginate --slurp` output (array of pages) to a single item list.
 * Also accepts an already-flat array (compat if --slurp omitted).
 * @param {unknown} pages
 * @returns {any[]}
 */
export function flattenPaginated(pages) {
  if (!Array.isArray(pages)) {
    return [];
  }
  if (pages.length > 0 && Array.isArray(pages[0])) {
    return pages.flat();
  }
  return pages;
}
