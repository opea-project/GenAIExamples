# Contributing

## License

Generative AI Examples is licensed under the terms in [LICENSE](/LICENSE).
By contributing to the project, you agree to the license and copyright terms therein and release your contribution under these terms.

## Create Pull Request

If you have improvements to Generative AI Examples, send your pull requests for
[review](https://github.com/opea-project/GenAIExamples/pulls).
If you are new to GitHub, view the pull request [How To](https://help.github.com/articles/using-pull-requests/).

### Step-by-Step guidelines

- Star this repository using the button `Star` in the top right corner.
- Fork this Repository using the button `Fork` in the top right corner.
- Clone your forked repository to your pc.
  `git clone "url to your repo"`
- Create a new branch for your modifications.
  `git checkout -b new-branch`
- Add your files with `git add -A`, commit with `git commit -s -m "This is my commit message"` and push `git push origin new-branch`.
- Create a [pull request](https://github.com/opea-project/GenAIExamples/pulls).

## Pull Request Template

See [PR template](/.github/pull_request_template.md)

## Pull Request Acceptance Criteria

- At least two approvals from reviewers

- All detected status checks pass

- All conversations solved

- Third-party dependency license compatible

## Pull Request Status Checks Overview

Generative AI Examples use [Actions](https://github.com/opea-project/GenAIExamples/actions) for CI test.
| Test Name | Test Scope | Test Pass Criteria |
|-------------------------------|-----------------------------------------------|---------------------------|
| Security Scan | Dependabot/Bandit | PASS |
| Format Scan | pre-commit.ci | PASS |
| Examples Test | Cases under Examples/tests folder | PASS |
| DCO | Use `git commit -s` to sign off | PASS |

> Notes: [Developer Certificate of Origin (DCO)](https://en.wikipedia.org/wiki/Developer_Certificate_of_Origin), you must agree to the terms of Developer Certificate of Origin by signing off each of your commits with `-s`, e.g. `git commit -s -m 'This is my commit message'`.

## Support

Submit your questions, feature requests, and bug reports to the [GitHub issues](https://github.com/opea-project/GenAIExamples/issues) page.
