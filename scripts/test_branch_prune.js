/** Offline contract test for the repository's merged-branch cleanup workflow. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const file = fs.readFileSync(path.join(__dirname, '../.github/workflows/prune-merged-branches.yml'), 'utf8');
const source = file.split('          script: |\n')[1];
assert(source, 'The cleanup workflow must define its GitHub script');
const code = source.split('\n').map(line => line.startsWith('            ') ? line.slice(12) : line).join('\n');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

async function check() {
  const deleted = [];
  const failures = [];
  const branches = [
    { name: 'main', commit: { sha: 'main' }, protected: false },
    { name: 'feat/merged', commit: { sha: 'abc' }, protected: false },
    { name: 'chore/merged', commit: { sha: 'def' }, protected: false },
    { name: 'feat/wip', commit: { sha: 'ghi' }, protected: false },
    { name: 'feat/changed-after-merge', commit: { sha: 'new' }, protected: false },
    { name: 'feat/other-repo', commit: { sha: 'jkl' }, protected: false },
    { name: 'feat/protected', commit: { sha: 'pqr' }, protected: true },
    { name: 'personal', commit: { sha: 'xyz' }, protected: false },
  ];
  const pr = (ref, sha, merged = true, fullName = 'VickMASpc/MellowStudio') => ({
    merged_at: merged ? '2026-10-28T13:00:00Z' : null,
    base: { ref: 'main' },
    head: { ref, sha, repo: { full_name: fullName } },
  });
  const prs = [
    pr('feat/merged', 'abc'),
    pr('chore/merged', 'def'),
    pr('feat/wip', 'ghi', false),
    pr('feat/changed-after-merge', 'old'),
    pr('feat/other-repo', 'jkl', true, 'SomeoneElse/Fork'),
    pr('feat/protected', 'pqr'),
  ];
  const github = {
    paginate: async (method) => {
      if (method === github.rest.repos.listBranches) return branches;
      if (method === github.rest.pulls.list) return prs;
      throw new Error('Unexpected API call');
    },
    rest: {
      repos: { get: async () => ({ data: { default_branch: 'main' } }), listBranches: () => {} },
      pulls: { list: () => {} },
      git: { deleteRef: async ({ ref }) => { deleted.push(ref); } },
    },
  };
  const core = { info: () => {}, setFailed: msg => failures.push(msg) };
  await new AsyncFunction('context', 'github', 'core', code)({ repo: { owner: 'VickMASpc', repo: 'MellowStudio' } }, github, core);
  assert.deepEqual(deleted.sort(), ['heads/chore/merged', 'heads/feat/merged']);
  assert.deepEqual(failures, []);
  console.log('Branch janitor contract OK: only exact-head, same-repo merged branches deleted.');
}
check().catch(e => { console.error(e); process.exitCode = 1; });
