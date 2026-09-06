# Ideas

These improvements are intentionally outside the technical assessment scope.

- Move JWT persistence from `localStorage` to secure `HttpOnly` cookies with the
  corresponding CSRF protections.
- Add continuous integration for backend and frontend quality checks, migration
  drift, PostgreSQL tests, and production builds.
- Add coverage reporting and query-count regression tests for detail and
  favorites endpoints with larger related datasets.
- Provide production-specific containers with non-root users, immutable base
  image digests, a production application server, and managed secrets.
- Split frontend routes into lazy-loaded bundles and lazy-load catalogue poster
  images to reduce the initial download and large-page network cost.
- Add a spectator account area for managing favorites and reviewing personal
  film and author ratings.
