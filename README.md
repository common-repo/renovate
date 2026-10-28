# renovate

A [common-repo](https://github.com/common-repo/common-repo) source template
that runs self-hosted [Renovate](https://docs.renovatebot.com/) to keep a
repo's `.common-repo.yaml` upstream refs current. Each bump moves the `ref:`
to the newest tag and runs `common-repo apply`, so the PR carries the
upstream's changes along with the ref.

## What's Included

| File | Purpose |
|---|---|
| `.github/workflows/renovate.yaml` | Daily Renovate run as a GitHub App, plus a manual dispatch with a `dry-run` input (default on) |
| `.github/renovate-global.json` | Global config: common-repo ref detection, the `common-repo apply` post-upgrade task, and defaults |

## Usage

> Requires common-repo ≥ 0.37.7.

```yaml
- repo:
    url: https://github.com/common-repo/renovate
    ref: v0.1.0
    with:
      - template-vars:
          GH_APP_ID_SECRET: MY_APP_ID      # name of the secrets.* entry holding the App ID
          GH_APP_KEY_SECRET: MY_APP_KEY    # name of the secrets.* entry holding the private key
          GH_APP_OWNER: my-org             # owner the App is installed on
          RENOVATE_EXTRA_REPOSITORIES: private-upstream
```

Add it once. After that, Renovate opens a PR whenever any upstream in the
file, including this one, has a newer tag.

### Prerequisites

- A **GitHub App** installed on the repo and on every private upstream the
  repo inherits from, directly or transitively. It needs contents, pull
  requests, issues and workflows write, and checks and statuses read.
  Workflows write is required because `common-repo apply` rewrites files
  under `.github/workflows/`.
- Normal review on Renovate PRs. A bump runs whatever the new upstream tag
  delivers, including workflow changes, so only inherit from upstreams you
  trust and don't let these PRs merge without review.

## Template Variables

| Variable | Default | Purpose |
|---|---|---|
| `GH_APP_ID_SECRET` | `COMMON_REPO_BOT_CLIENT_ID` | Name of the `secrets.*` entry holding the App ID or Client ID |
| `GH_APP_KEY_SECRET` | `COMMON_REPO_BOT_PRIVATE_KEY` | Name of the `secrets.*` entry holding the App private key |
| `GH_APP_OWNER` | `common-repo` | Owner the App is installed on |
| `RENOVATE_EXTRA_REPOSITORIES` | empty | Comma-separated private upstreams under `GH_APP_OWNER`. The token always covers the current repo |
| `RENOVATE_CRON` | `17 6 * * *` | Schedule for the daily run |
| `RENOVATE_LOG_LEVEL` | `info` | Renovate `LOG_LEVEL` |
| `COMMON_REPO_VERSION` | `v0.37.7` | common-repo CLI used by the post-upgrade `apply` |

Values are secret *names*, never secret values. These are the same three
App variables [semantic-release](https://github.com/common-repo/semantic-release#template-variables)
uses, so a repo that inherits both can set them once at the top level.

Private upstreams must belong to `GH_APP_OWNER`. One installation token
can't reach another owner's private repos.

## How it works

The workflow checks out only `.github/renovate-global.json`, mints an App
token for the repo plus `RENOVATE_EXTRA_REPOSITORIES`, installs the pinned
common-repo CLI, and runs the Renovate action against the current repo.
The token covers the tag lookups and the clones `common-repo apply` does
during the post-upgrade task.

The global config sets:

- `onboarding: false` and `requireConfig: optional`. The repo doesn't need a
  `renovate.json`.
- `allowedCommands: ["^common-repo apply$"]`. No other post-upgrade command
  can run.
- Two regex managers with `depType: common-repo`, and a package rule that
  runs `common-repo apply` for that depType only.
- `enabledManagers: ["custom.regex"]` as a default, so adding this upstream
  doesn't start Renovate PRs for npm, Go, Actions and so on.

The config ships whole and is replaced, not merged, on every bump. Old rules
don't pile up across versions.

### Customizing

A repo's own Renovate config (`renovate.json` or any other
[config location](https://docs.renovatebot.com/configuration-options/))
layers on top of the global config. `customManagers` and `packageRules` are
added to the global ones, and other settings override the defaults. For
example:

```json
{
  "extends": ["config:recommended"],
  "enabledManagers": ["custom.regex", "gomod"],
  "packageRules": [
    { "matchDepTypes": ["common-repo"], "semanticCommitType": "fix" }
  ]
}
```

- If you set `enabledManagers`, keep `custom.regex` in it, or common-repo
  refs stop updating.
- Commit type: Renovate uses `chore` unless the repo config says
  otherwise. Set `semanticCommitType: fix` for `common-repo` deps if an
  upstream bump should cut a patch release, which is usually what a template
  repo wants.

## Supported `.common-repo.yaml` syntax

Detected: `url:` and `ref:` keys of the same `repo:` entry, in either order,
with only blank or comment lines between them. URLs must be
`https://github.com/<owner>/<repo>`, quoted or not, with or without `.git`.
Refs can be quoted or bare, with a trailing comment. Refs are looked up as
GitHub tags.

Not detected or not updated: flow-style maps (`{url: ..., ref: ...}`), other
keys between `url:` and `ref:`, SSH or non-GitHub URLs, and local paths.
Branch and commit refs are found but have no newer tag, so they're left
alone. `tests/fixtures/` lists the cases the tests cover.

## Runtime versions

The common-repo CLI is pinned (`COMMON_REPO_VERSION`) because Renovate
commits whatever `apply` produces. The Renovate action is pinned by SHA,
but it runs the floating `44` image tag, so the Renovate version inside a
major can change between runs.

## Development

Validate with `common-repo validate`, `common-repo apply --dry-run`,
`prek run --all-files` and `script/test`. `script/test` skips the
Renovate validation and the consumer fixture when `renovate-config-validator`
or `common-repo` is missing. The Consumer fixture workflow installs both and
sets `REQUIRE_TOOLS=1`, so nothing is skipped in CI.
