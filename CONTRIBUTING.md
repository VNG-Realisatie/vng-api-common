# Contributing to vng-api-common

Hi! First of all, thank you for your interest in contributing to this project,
you can do this in a number of ways :-)

* [Reporting issues](#reporting-issues)
* [Submitting pull requests](#submitting-pull-requests)
* [Code and commit style](#code-and-commit-style)

## Versioning

vng-api-common is used as shared library in various downstream projects, which
each have their own versions (currently they are all in 1.0.0 release
candidate) status.

The versioning of vng-api-common is semantic and follows the downstream
versioning. This means that the current latest version can accept new features,
i.e. things that make the API look different, in non-breaking ways, such as
adding API resource field attributes.

Current branches/versions:

* `master` is the latest version, currently tracking `1.1.x` versions.
* `stable/1.0.x` is input for the 1.0.0 release candidate versions.

## Reporting issues

If you're running into a bug or desired feature, you can
[submit an issue](https://github.com/VNG-Realisatie/vng-api-common/issues/new).

**Feature requests**

When you're submitting a feature request, please use the label *enhancement*.

**Submitting a bug report**

When submitting a bug report, please state:

1. Which API this occurred in (ZRC, DRC, ...)
2. What the expected behaviour was
3. What the observed behaviour is

If the issue affects older versions, please apply those tags (e.g. *1.0.x*)

## Submitting pull requests

Code contributions are valued, but we request some quality control!

**Tests**

Please make sure the tests pass. You can run the test suite by running `tox`.
While developing, you can also run the tests using `pytest` in the root of the
project. See the Tox and Pytest documentation for advanced usage.

You can also refer to the `.travis.yml` setup to see which system requirements
are relevant, such as a working Postgres database.

Bugfixes require a test that shows the errant behaviour and proves the bug was
fixed.

New features should be accompanied by tests that show the interface/desired
behaviour.

## Code and commit style

**Imports**

We sort imports using [isort](https://pypi.org/project/isort/). The tests
have an `isort` check, which you can run using `tox -e isort`.

**Code formatting**

Python code should be [black](https://github.com/psf/black) formatted, this
leaves no discussion about formatting.

**Commit messages**

Please use meaningful commit messages, and rebase them if you can. For example,
we'd expect a commit for adding a regression test and a second commit with
the fix.

We encourage use of [gitmoji](https://gitmoji.carloscuesta.me/) to quickly
identify the type of change in the commit. This also helps you keep your
commits atomic - if multiple gitmoji are applicable, perhaps your commit should
be split in multiple atomic commits.

Where applicable, please refer to the reported issue.

Commit message template:

```
:bug: Fixes #123 -- fixed URL resolution

<elaborate description describing what happened in the commit>
```
