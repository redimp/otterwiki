# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [v2.5.1](https://github.com/redimp/otterwiki/releases/tag/v2.5.1) - 2024-08-06

<small>[Compare with v2.5.0](https://github.com/redimp/otterwiki/compare/v2.5.0...v2.5.1)</small>

### Features

- Feature: Added buttons to toggle pagename prefix to the rename page form.

### Bug Fixes

- Fix: Typo in the label of the hide the logo checkbox.

## [v2.5.0](https://github.com/redimp/otterwiki/tags/v2.5.0) - 2024-08-02

<small>[Compare with v2.4.4](https://github.com/redimp/otterwiki/compare/v2.4.4...v2.5.0)</small>

### Features

- Improved the Edit/Preview implementation, see [#67](https://github.com/redimp/otterwiki/issues/67).
- Warn user when navigating away from unsaved changes, see [#64](https://github.com/redimp/otterwiki/issues/64).
- Added auto save (as draft) feature to the editor, see [#66](https://github.com/redimp/otterwiki/issues/66).
- Added option to hide the logo of An Otter WIki from the Sidebar as discussed in [#127](https://github.com/redimp/otterwiki/discussions/127).
- Improve page view/toc: highlight current position in the toc.
- Display human friendly timedeltas like "17 minutes and 4 secs ago" in the `title=` of the history and changelog dates.

## [v2.4.4](https://github.com/redimp/otterwiki/tags/v2.4.4) - 2024-07-10

<small>[Compare with v2.4.3](https://github.com/redimp/otterwiki/compare/v2.4.3...v2.4.4)</small>

### Features

- Sidebar on small screen (mobile devices) will not expaned but overlay [#124](https://github.com/redimp/otterwiki/issues/124)
- Better CSS for media: print [#126](https://github.com/redimp/otterwiki/issues/126)
- Part of the release are slim images, built with only uWSGI, without nginx and supervisord based on alpine 3.20.1. Running as unpriviliged user, listening on port 8080. docker image tags get -slim appended e.g. `redimp/otterwiki:2.4.4-slim` [#121](https://github.com/redimp/otterwiki/issues/121)

## [v2.4.3](https://github.com/redimp/otterwiki/tags/v2.4.3) - 2024-06-16

<small>[Compare with v2.4.2](https://github.com/redimp/otterwiki/compare/v2.4.2...v2.4.3)</small>

### Features

- Easier page structuring: In /-/create the most recent visited pages can be added to the pages path, as discussed in [#113](https://github.com/redimp/otterwiki/discussions/113).
- plugins can be loaded in the docker image via /plugins and /app-data/plugins.

### Bug Fixes

- Removed the revert icon/button for users without WRITE permission from history and changelog.
- Extended the plugin "documentation" in [docs/plugin_examples](https://github.com/redimp/otterwiki/tree/main/docs/plugin_examples), the lack of documentation was brought up in [#119](https://github.com/redimp/otterwiki/issues/119).

## [v2.4.2](https://github.com/redimp/otterwiki/tags/v2.4.2) - 2024-05-21

<small>[Compare with v2.4.1](https://github.com/redimp/otterwiki/compare/v2.4.1...v2.4.2)</small>

### Features

- Raise an error if no `SECRET_KEY` is set [#115](https://github.com/redimp/otterwiki/issues/115)

### Bug Fixes
- Fixed Page names capitalization in Sidebar [#117](https://github.com/redimp/otterwiki/issues/117)

### Dependencies

- Bump werkzeug from 3.0.1 to 3.0.3, jinja2 from 3.1.3 to 3.1.4 by [@dependabot](https://github.com/dependabot)

## [v2.4.1](https://github.com/redimp/otterwiki/tags/v2.4.1) - 2024-04-29

<small>[Compare with v2.4.0](https://github.com/redimp/otterwiki/compare/v2.4.0...v2.4.1)</small>

### Features

- Added a Helm chart for OtterWiki by [@baldy-cape](https://github.com/baldy-cape) in [#106](https://github.com/redimp/otterwiki/pull/106), see the charts [README](https://github.com/redimp/otterwiki/tree/main/helm) for instructions.

### Bug Fixes

- Fixed handling of bool values when configuring via environment variables
- Fixed log when renaming has failed

### Dependencies

- Bump pillow from 10.2.0 to 10.3.0 by [@dependabot](https://github.com/dependabot) in #104
- Bump pluggy from 1.4.0 to 1.5.0

## [v2.4.0](https://github.com/redimp/otterwiki/tags/v2.4.0) - 2024-03-23

<small>[Compare with v2.3.0](https://github.com/redimp/otterwiki/compare/v2.3.0...v2.4.0)</small>

### Features

- Proof of concept for reverse-proxy auth by @weaversam8 in [#95](https://github.com/redimp/otterwiki/pull/95) [#90](https://github.com/redimp/otterwiki/issues/90)
- Added CSS Tweaking/Custom Theming [#101](https://github.com/redimp/otterwiki/issues/101)
- editor: added highlighting in fenced code blocks for haskell, lua, jinja2 and ruby

### Bug Fixes

- editor: Fixed low contrast of comments in fenced code in dark-mode [#103](https://github.com/redimp/otterwiki/issues/103)

### Refactored

- Configuration via environment variables is on in otterwiki.server

## [v2.3.0](https://github.com/redimp/otterwiki/tags/v2.3.0) - 2024-03-13

<small>[Compare with v2.2.0](https://github.com/redimp/otterwiki/compare/v2.2.0...v2.3.0)</small>

### Features

- Proof of concept for plugins by [@weaversam8](https://github.com/weaversam8) in [#96](https://github.com/redimp/otterwiki/pull/96)
- Allow disabling of registration by [@Hellrespawn](https://github.com/Hellrespawn) in [#98](https://github.com/redimp/otterwiki/pull/98)
- The searchbar got a hotkey: / ( [#93](https://github.com/redimp/otterwiki/issues/93) )
- Editor has now built-in Find and Replace via hotkeys and toolbar ( [#63](https://github.com/redimp/otterwiki/issues/63) )

## [v2.2.0](https://github.com/redimp/otterwiki/tags/v2.2.0) - 2024-03-03

<small>[Compare with v2.1.0](https://github.com/redimp/otterwiki/compare/v2.1.0...v2.2.0)</small>

### Features

- added: support for case sensitive page names [#85](https://github.com/redimp/otterwiki/issues/85) by [@weaversam8](https://github.com/weaversam8)
- added: sync with git repositories via git http as discussed in [#87](https://github.com/redimp/otterwiki/discussions/87)

## [v2.1.0](https://github.com/redimp/otterwiki/tags/v2.1.0) - 2024-02-18

<small>[Compare with v2.0.5](https://github.com/redimp/otterwiki/compare/v2.0.5...v2.1.0)</small>

### Features

- added: Allow empty commit messages #81
- added: The Sidemenu can be configured to display the Page Index as tree, as requested in [#70](https://github.com/redimp/otterwiki/issues/70) and discussed in [#60](https://github.com/redimp/otterwiki/discussions/60) . @Ritzelprimpf is largely responsible for the design.
- added: Display the full path when renaming a page.
- added: Admins can now configure that users get a notification mail on approval, as requested in #7

### Misc

- Proofreading by @Ritzelprimpf

## [v2.0.5](https://github.com/redimp/otterwiki/tags/v2.0.5) - 2024-02-10

<small>[Compare with v2.0.4](https://github.com/redimp/otterwiki/compare/v2.0.4...v2.0.5)</small>

### Features

- redesigned the pageindex, adapts better to different screen widths (fixes [#80](https://github.com/redimp/otterwiki/issues/80)), ordered like a book now, vertical columns are filled first.

## [v2.0.4](https://github.com/redimp/otterwiki/tags/v2.0.4) - 2024-01-24

<small>[Compare with v2.0.3](https://github.com/redimp/otterwiki/compare/v2.0.3...v2.0.4)</small>

### Bug Fixes

- Fix broken urls in the links of headings on the pageindex. Fixes [#78](https://github.com/redimp/otterwiki/issues/78).

## [v2.0.3](https://github.com/redimp/otterwiki/tags/v2.0.3) - 2024-01-22

<small>[Compare with v2.0.2](https://github.com/redimp/otterwiki/compare/v2.0.2...v2.0.3)</small>

### Bug Fixes

- Renaming pages into subdirectories fixed
- Search results got better highlighting [#76](https://github.com/redimp/otterwiki/issues/76)

### Dependencies

- Bump jinja2 from 3.1.2 to 3.1.3 by [@dependabot](https://github.com/dependabot) in [#74](https://github.com/redimp/otterwiki/pull/74)
- Bump pillow from 10.0.1 to 10.2.0 by [@dependabot](https://github.com/dependabot) in [#77](https://github.com/redimp/otterwiki/pull/77)

## [v2.0.2](https://github.com/redimp/otterwiki/tags/v2.0.2) - 2024-01-10

<small>[Compare with v2.0.1](https://github.com/redimp/otterwiki/compare/v2.0.1...v2.0.2)</small>

### Dependencies

- Bump gitpython from 3.1.37 to 3.1.41 by @dependabot in [#73](https://github.com/redimp/otterwiki/pull/73)

## [v2.0.1](https://github.com/redimp/otterwiki/tags/v2.0.1) - 2023-12-30

<small>[Compare with v2.0.0](https://github.com/redimp/otterwiki/compare/v2.0.0...v2.0.1)</small>

### Features

- Page titles (upper and lowercase) are now derived from the first header. e.g. `Mathjax` vs [MathJax](https://otterwiki.com/Examples/MathJax)  This was brought up and discussed in [#61](https://github.com/redimp/otterwiki/issues/61)
- Toggling the sidebar stores the state and keeps it until toggled again (no more sidebar flashing on mobile and small screens)

### Bug Fixes

- Fixed http headers for attached files to improve attachment caching
- The `A-Z` page index has been tweaked to better display pages grouped in subdirectories

## [v2.0.0](https://github.com/redimp/otterwiki/tags/v2.0.0) - 2023-12-04

### Features

* Editor with markdown support
* Fine tuned the minimal design and the syntax highlighting
* Additions to the common markdown syntax like
  * footnotes
  * check lists
* Uncommon additions like
  * spoiler and folded blocks.
