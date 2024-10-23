# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [v2.7.0](https://github.com/redimp/otterwiki/releases/tag/v2.7.0) - 2024-10-24

<small>[Compare with v2.6.2](https://github.com/redimp/otterwiki/compare/v2.6.2...v2.7.0)</small>

### Features

- added "Add User" functionality to user management, see #151. ([ca5360f](https://github.com/redimp/otterwiki/commit/ca5360fe45dbcae11b0deb1caef658f76a114cea)).
- added copy-to-clipboard button to code blocks, see #153. ([68f82f6](https://github.com/redimp/otterwiki/commit/68f82f682d3ad78235c1232b9c140b1146f0a84f)).
- option for disable commit added and respected in editor ([0da52ff](https://github.com/redimp/otterwiki/commit/0da52ffccd7ad45c11a497ab39f4b7c6f2625dd4)).

### Bug Fixes

- `has_permission` must use `self.has_permission` to work correct with git ([190a622](https://github.com/redimp/otterwiki/commit/190a622dcc2761a95a339a5add4f1239649b3509)), this fixes #154.

## [v2.6.2](https://github.com/redimp/otterwiki/releases/tag/v2.6.2) - 2024-10-10

<small>[Compare with v2.6.1](https://github.com/redimp/otterwiki/compare/v2.6.1...v2.6.2)</small>

### Bug Fixes

- wikilink re-implemented as inline parser not plugin, see #144 ([32299d0](https://github.com/redimp/otterwiki/commit/32299d0d59b7649da27e4093a1b9f4f829989f63)).
- better margins for tables and pre blocks ([f31e7ef](https://github.com/redimp/otterwiki/commit/f31e7ef856532e915f9bbf04fffb83d6b277a66b)).
- breadcrumbs in a /-/commit/ uses filepath not pagepath ([6726412](https://github.com/redimp/otterwiki/commit/67264121ab51b83b7e4164b49ba89cd380eae4c6)).
- diffs on files without a newline at the end are displayed correctly ([561ed88](https://github.com/redimp/otterwiki/commit/561ed88070fe520a0809863fb2c8dd380b80253d)).

### Code Refactoring

- `update_mermaid()` does exactly that. diagrams in documentation as svgs. ([12d3c00](https://github.com/redimp/otterwiki/commit/12d3c00fd71ef5019733d96bb9fadc3fa9042dfe)).

## [v2.6.1](https://github.com/redimp/otterwiki/releases/tag/v2.6.1) - 2024-09-29

<small>[Compare with v2.6.0](https://github.com/redimp/otterwiki/compare/v2.6.0...v2.6.1)</small>

### Design/Behaviour changes

- Disabled auto-scaling ([003975a](https://github.com/redimp/otterwiki/commit/003975a73f6bfabd55e24736f1be6e580ffd49d1)).

### Features

- In mermaid blocks replace `\n` with `<br/>` ([0d52932](https://github.com/redimp/otterwiki/commit/0d5293273472526742a5e61f4efb06972b3146a3)).

### Bug Fixes

- initialize mermaid after DOM being ready ([1b5187d](https://github.com/redimp/otterwiki/commit/1b5187dcc374283660d0f08d158d4d8c22b44a97)).
- typo, more visibility for fatal errors, no endless failure loop ([acf7b3b](https://github.com/redimp/otterwiki/commit/acf7b3b29e5c2d716e640933a9f327e46b9d40e1)).

## [v2.6.0](https://github.com/redimp/otterwiki/releases/tag/v2.6.0) - 2024-09-15

<small>[Compare with v2.5.2](https://github.com/redimp/otterwiki/compare/v2.5.2...v2.6.0)</small>

### Features

- Added Custom Sidebar Menu, see #125 ([be3c4a5](https://github.com/redimp/otterwiki/commit/be3c4a59ba0f5ae06d7ef1a02b3a7feb4b6f5207)).
- Sidebar shortcuts are configurable, see #125. ([d2a617e](https://github.com/redimp/otterwiki/commit/d2a617e2607d5657393d77fe10dab7e2ab279bc6)).
- Added support for Mermaid diagrams, see #138. ([ed0e06f](https://github.com/redimp/otterwiki/commit/ed0e06fe0b87034db4b1400138f87acbacef7779)).
- Alerts are now supported by the markdown renderer ([1a88ab8](https://github.com/redimp/otterwiki/commit/1a88ab89b2a235502bcb7d210dc80c1e1fb5f251)).
- Configure in the preferences whether robots are allowed to crawl the wiki, see #133. ([99862d](https://github.com/redimp/otterwiki/commit/99862da37c06225e321101b6a67748039e99b6b4)).
- Redesigned the admin interface. ([d2a617e](https://github.com/redimp/otterwiki/commit/d2a617e2607d5657393d77fe10dab7e2ab279bc6)).
- Page/history and Page/blame make better use of space. Improved blame display. ([20a33d2](https://github.com/redimp/otterwiki/commit/20a33d2dacbcdd69c91c67b89605d95820737881)).

### Bug Fixes

- removed obsolete `_db_migrate()` function from `SimpleAuth`. ([f89829d](https://github.com/redimp/otterwiki/commit/f89829d9af5dba339b437bc343cb02b36096dc6e)).
- edit/preview: remove misplaced cursormagicword from toc ([1a91c50](https://github.com/redimp/otterwiki/commit/1a91c5030ebaf715f9f4a3a8e742a241e039f31e)).
- inconsistent font size in special blocks, see #136 ([44a308b](https://github.com/redimp/otterwiki/commit/44a308bd6e5593cb268c26b284d9edc3523b9351)).
- QoL Changelog uses full column and displays the menutree. ([2e9927d](https://github.com/redimp/otterwiki/commit/2e9927d1a21baaee16f2a3a329bb6a7525142c61)).
- added meta robots: noindex, nofollow to changelog, forms and page revisions ([0f95755](https://github.com/redimp/otterwiki/commit/0f95755e488d15026c24819c5a609fc4c0397cc9)).

### Code Refactoring

- custom_menu list of dicts instead of list of lists ([3cb2021](https://github.com/redimp/otterwiki/commit/3cb20214db09dcc2cc3b46b53398166b466cc692)).

## [v2.5.2](https://github.com/redimp/otterwiki/releases/tag/v2.5.2) - 2024-08-15

<small>[Compare with v2.5.1](https://github.com/redimp/otterwiki/compare/v2.5.1...v2.5.2)</small>

### Features

- Quality of life improvements for Changelog, History and Diff views ([d73aefe](https://github.com/redimp/otterwiki/commit/d73aefe0f09aaf4a094c3711e19ffc8107796572) and [0f20d98](https://github.com/redimp/otterwiki/commit/0f20d98d99f798897742ca423eaa92dff18c8039)).

### Bug Fixes

- Removed the necessity that a page exists to get an attachment ([455497e](https://github.com/redimp/otterwiki/commit/455497e03cf8c805e9e27bbd3e4e77caefe57ca7)).
- Remove current page from list of prefixes when renaming ([af5bbd2](https://github.com/redimp/otterwiki/commit/af5bbd2943f03f55be35262e3e937069b04f00ef)).
- Hitting [ENTER] submits the form in create and rename. ([a6cde65](https://github.com/redimp/otterwiki/commit/a6cde65e808ab03eb2fda29530c6def1f89c75ce)).

### Code Refactoring

- menutree does not depend on pagepath being set ([0136a83](https://github.com/redimp/otterwiki/commit/0136a83bb9c1396f1249dc0876b2d4bf0f389656)).
- removed unused filename parameter from diff() ([008a562](https://github.com/redimp/otterwiki/commit/008a5625dbca8566b5f16408eba4aa97862a91a1)).

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
