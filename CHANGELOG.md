# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [v2.17.2](https://github.com/redimp/otterwiki/releases/tag/v2.17.2) - 2026-02-11

<small>[Compare with v2.17.1](https://github.com/redimp/otterwiki/compare/v2.17.1...v2.17.2)</small>

### Bug Fixes

- Enable `/` hotkey for keyboard layouts needing shift to type '/', see #383 ([6ee5592](https://github.com/redimp/otterwiki/commit/6ee55922ca68f8c9d47e5d8fba31f57bad23a8b8) by @redimp).
- preserve (and display) multiple spaces in codespans, see #382 ([0f669d8](https://github.com/redimp/otterwiki/commit/0f669d8f6033b74b4d0e6d60e73815a99ca4998d) by @redimp).
- confusing editor behaviour on URL pasting, see #380 ([2f73bdf](https://github.com/redimp/otterwiki/commit/2f73bdfa45df4b18d72dac59c241f6332f90f499) by @deseven).

### Plugins

- `plugin_redlinks`: fixed page lowercase logic, see #376 ([0d4b80c](https://github.com/redimp/otterwiki/commit/0d4b80cf46a004307b53eb926fc65f7e12b36f89) by @freddyheppell)

## [v2.17.1](https://github.com/redimp/otterwiki/releases/tag/v2.17.1) - 2026-02-02

### Bug Fixes

- fixed broken syntax page ([bc2da8b](https://github.com/redimp/otterwiki/commit/bc2da8bd03d4b03da04298f0982a201396f0ddbf) by @deseven)
- redirect not logged in users to the login page where applicable ([8b9289d](https://github.com/redimp/otterwiki/commit/8b9289d8939b6f0ae206ec2e6ea76d58f9e23bf6) by @deseven)

<small>[Compare with v2.17.0](https://github.com/redimp/otterwiki/compare/v2.17.0...v2.17.1)</small>

## [v2.17.0](https://github.com/redimp/otterwiki/releases/tag/v2.17.0) - 2026-02-01

<small>[Compare with v2.16.0](https://github.com/redimp/otterwiki/compare/v2.16.0...v2.17.0)</small>

### Features

- custom home page, see #354 ([16e1a94](https://github.com/redimp/otterwiki/commit/16e1a94212e1cf0981d20e898c242ce0e598afbc) by @deseven).
- Editor: Add Wikilinks with Title, see #357 and #358 ([466c338](https://github.com/redimp/otterwiki/pull/358/changes/466c338fc2827a55253d7bd24c286cda917c4c45) by @ryanwhowe)
- plugin hook for Wikilinks rendering and example plugin, see #363 ([6d20a5a](https://github.com/redimp/otterwiki/commit/6d20a5adede14ddfd9d445139b9e65d6e1fc3d5a) by @deseven).
- added hotkey `]` to toggle the right extra sidebar, see #366 ([4ec484e](https://github.com/redimp/otterwiki/commit/4ec484e5542801676a782bdf9e3dcade622a0764)).
- page blame: add the commit message for a better blame view, see #367 ([f51965e](https://github.com/redimp/otterwiki/commit/f51965e6d4ae8507bc1fcf9809a2c0ab8e3961a6)).

### Bug Fixes

- title-bar `SITE_NAME` title changed to `SITE_DESCRIPTION`, see #356 ([85a110d](https://github.com/redimp/otterwiki/commit/85a110dd0362fbf1b96aa466e2fc90679fd5dbe4)).
- icon alignments in sidebar, see #362 ([db70758](https://github.com/redimp/otterwiki/pull/362/changes/db707580274bddbf224612bbee5a098f9831f810) by @tvanas)
- lowercase GitHub-style alerts, see #360 ([1c6876d](https://github.com/redimp/otterwiki/pull/360/changes/1c6876dafb7718180d5ef3cf33da76ccfd7fcda2) by @aimileus)

## [v2.16.0](https://github.com/redimp/otterwiki/releases/tag/v2.16.0) - 2026-01-18

<small>[Compare with v2.15.2](https://github.com/redimp/otterwiki/compare/v2.15.2...v2.16.0)</small>

### Features

- Syncing with remote repositories, see `Settings > Repository Management`.
  - automatic pulling from from the defined git remote ([111c5c1](https://github.com/redimp/otterwiki/commit/111c5c1043c12b7dfd11de31954583e3cf8193a6) by @deseven).
  - automatic pushing to the defined git remote ([8d10cc6](https://github.com/redimp/otterwiki/commit/8d10cc6d299c6d64a71f31d64a9b0acba54aefe9) by @deseven).
  - repository management manual actions ([6c89261](https://github.com/redimp/otterwiki/commit/6c892612ac8442bf4231ec213afcacd26fc9563a) by @deseven).
- More options to customize the wiki using custom css
  - added classes with levels to the pageindex items ([91d797e](https://github.com/redimp/otterwiki/commit/91d797eebc5f25621f138f323608eddd8d82fb5b)).
  - support custom fancy block styles, see #345 and #343 ([fde2bf6](https://github.com/redimp/otterwiki/pull/345/commits/fde2bf68bf05011d35a9fa4e4967db79ca636f30) by @freddyheppell).
  - make pages customizable via css based on their pathname ([PR#349](https://github.com/redimp/otterwiki/pull/349) by @freddyheppell).
- Improving the plugin environment
  - added more plugin hooks for html injection & processing ([7f0fcbc](https://github.com/redimp/otterwiki/pull/336/commits/7f0fcbc7feb2260f4800df382309804d1f5120ff) by @deseven).

### Bug Fixes

- better preview cursor placement, see #330 ([0797796](https://github.com/redimp/otterwiki/commit/079779671934e53c294875c2f4ac45d257f3f457)).
- scrollbar styling for `width<=768px`, see #332 ([562edac](https://github.com/redimp/otterwiki/commit/562edac8d25d7baadea5c001f155765588a73ea7)).
- `sanitize_pagename(.., handle_md=True)` regexp fixed, see #344 ([bed5cc5](https://github.com/redimp/otterwiki/commit/bed5cc551920cf8eef14dc82c10704eb5cc80863)).

## [v2.15.2](https://github.com/redimp/otterwiki/releases/tag/v2.15.2) - 2026-01-07

<small>[Compare with v2.15.1](https://github.com/redimp/otterwiki/compare/v2.15.1...v2.15.2)</small>

### Bug Fixes

- edit/preview switching while resizing the window works ([508b8fa](https://github.com/redimp/otterwiki/commit/508b8fa6150e650b7769dc2055098fb3ffa40f31)).
- slim-image: Configure uWSGI with environment variables ([3e3f6f2](https://github.com/redimp/otterwiki/commit/3e3f6f274a7b5424f7df3745e9d4364561b920af)).

## [v2.15.1](https://github.com/redimp/otterwiki/releases/tag/v2.15.1) - 2026-01-02

<small>[Compare with v2.15.0](https://github.com/redimp/otterwiki/compare/v2.15.0...v2.15.1)</small>

### Bug Fixes

- `load_custom_html` respects `USE_STATIC_PATH`, see #329 ([9da7cb4](https://github.com/redimp/otterwiki/pull/331/commits/9da7cb459c40a341ef86d9a82bac5b0120b0e21d))

## [v2.15.0](https://github.com/redimp/otterwiki/releases/tag/v2.15.0) - 2025-12-18

<small>[Compare with v2.14.4](https://github.com/redimp/otterwiki/compare/v2.14.4...v2.15.0)</small>

### Features

- Better Customization: custom head and body html from files ([e7b4aef](https://github.com/redimp/otterwiki/commit/e7b4aef0336befafba6975b0ba334ca953c6c53b) by deseven).
- The sidebar menu can now display icons and separators  ([128af8f](https://github.com/redimp/otterwiki/commit/128af8fcb2babd9e934cfc31c0cb58ca759c9b7c) by deseven).
- Improved head and meta data: canonical urls, meta description ([0754fe2](https://github.com/redimp/otterwiki/commit/0754fe2246d660834d166c87b66a0d4221fc80f7) by deseven).
- Improved Page loading: load mermaid and mathjax only when needed ([fa93a42](https://github.com/redimp/otterwiki/commit/fa93a421e3a0ae38cb91a88287a8491a892eae26) by deseven).

### Bug Fixes

- Renamed pages can now handle history and revisions, no more broken links after page rename ([1a8d890](https://github.com/redimp/otterwiki/commit/1a8d890f94e6226d5395e854f5afc3b7de988eb2) by deseven).

## [v2.14.4](https://github.com/redimp/otterwiki/releases/tag/v2.14.4) - 2025-12-06

<small>[Compare with v2.14.3](https://github.com/redimp/otterwiki/compare/v2.14.3...v2.14.4)</small>

### Bug Fixes

- custom jinja filter "urlquote" to handle quotes in page names ([954d02a](https://github.com/redimp/otterwiki/commit/954d02a010dd7a32cd08b22b3c7388ead39ac2e4) by Ralph Thesen).
- don't apply underscore replacement when renaming, allow only positive numbers for thumbnail size field ([9c6e3e8](https://github.com/redimp/otterwiki/commit/9c6e3e8ea4015cb5987eb173d3e7eeda381c68e4) by deseven).

## [v2.14.3](https://github.com/redimp/otterwiki/releases/tag/v2.14.3) - 2025-11-28

<small>[Compare with v2.14.2](https://github.com/redimp/otterwiki/compare/v2.14.2...v2.14.3)</small>

### Features

- added `sitemap.xml` [PR#314](https://github.com/redimp/otterwiki/pull/314) by [Ivan Novokhatski](https://github.com/deseven).
- add robots: `noindex, nofollow` to diff, source and commits, see #313 ([2ada269](https://github.com/redimp/otterwiki/commit/2ada269960cebac1489525a537a5219763715ecd)).
- added markdown abbreviation support, see #310 ([6b0df15](https://github.com/redimp/otterwiki/commit/6b0df155ce8cecef835fe8631f834ebbe88a5b88)), with documentation by [Wdavery](https://github.com/Wdavery), see [PR#312](https://github.com/redimp/otterwiki/pull/312).
- added support for using pagenames with _ instead of spaces, see [PR#316](https://github.com/redimp/otterwiki/pull/316) by  [Ivan Novokhatski](https://github.com/deseven).

### Bug Fixes

- single quotes in page names cause POSTs to fail, see #307 ([9e3d0de](https://github.com/redimp/otterwiki/commit/9e3d0dea04707452dd90d95bfe21f8238113a573)).

## [v2.14.2](https://github.com/redimp/otterwiki/releases/tag/v2.14.2) - 2025-11-09

<small>[Compare with v2.14.1](https://github.com/redimp/otterwiki/compare/v2.14.1...v2.14.2)</small>

### Features

- use the page header as html `<title>` ([947443d](https://github.com/redimp/otterwiki/commit/947443d279baed04c475f84994e017d5e256be41)).
- added button to editor to add a horizontal line to the document, see #299 ([b412d99](https://github.com/redimp/otterwiki/commit/b412d990765e2a8a5c619d6ada3376a4f41cbaa8)).

### Bug Fixes

- Make better use of the docker healthcheck, see #242 ([8bfb7a1](https://github.com/redimp/otterwiki/commit/8bfb7a17a39e1c148102aacf31d5c6ece8d65fac)).
- Fixed documentation about attachment handling, see #296.

## [v2.14.1](https://github.com/redimp/otterwiki/releases/tag/v2.14.1) - 2025-09-18

<small>[Compare with v2.14.0](https://github.com/redimp/otterwiki/compare/v2.14.0...v2.14.1)</small>

### Features

- auth headers can now be customized when using `AUTH_METHOD='PROXY_HEADER'`, see [PR#287](https://github.com/redimp/otterwiki/pull/287) by Kamil Essekkat @ekamil ([fb20d65](https://github.com/redimp/otterwiki/commit/fb20d65d14e37c7a894f9447c5d0c80d1c3ba8aa)).

### Bug Fixes

- `plugin_authorsignature` fixed: use git log for finding the page creation metadata, see #288 ([7bca4aa](https://github.com/redimp/otterwiki/commit/7bca4aa678bed4e5015ca7440c3f7604c8d41d35)).
- Changelog: log parsing for merge commits fixed ([28ea1f0](https://github.com/redimp/otterwiki/commit/28ea1f0f08fc6bad5f4b2448f5429aa26118beef)).

## [v2.14.0](https://github.com/redimp/otterwiki/releases/tag/v2.14.0) - 2025-08-31

<small>[Compare with v2.13.0](https://github.com/redimp/otterwiki/compare/v2.13.0...v2.14.0)</small>

### Features

- Adding wikilinks so that the editor sidebar now handles selected text,
  ([92489c7](https://github.com/redimp/otterwiki/pull/280/commits/92489c7f01cb7291ac5e0eaef15da2b291dcf731)), by @Harriotskelli, see [PR#280](https://github.com/redimp/otterwiki/pull/280)
- housekeeping: Drafts and empty pages, see #271 ([c8364d6](https://github.com/redimp/otterwiki/commit/c8364d637a370c5b1ddbe9cb195db6196cad0681)).
- image attachments can now be resized using `?size=` `?width=` and `?height=`, see #278 ([4fc77b5](https://github.com/redimp/otterwiki/commit/4fc77b592a2f117369df40c9f412c70b3ab60544)).
- added Docker HEALTHCHECKs ([dfe314d](https://github.com/redimp/otterwiki/commit/dfe314d2c8dc14cd2e1dd042d7cc7790f05f5998)).

### Plugins

- OtterWikiPluginSpec got the setup() hook ([18cd6af](https://github.com/redimp/otterwiki/commit/18cd6afbb50ffaef12109806f55eb358470944e6)).
- [docs/plugin_examples/plugin_authorsignature](https://github.com/redimp/otterwiki/tree/main/docs/plugin_examples/plugin_authorsignature)
  was improved by Benjamin Esquivel @tarxf, see [PR#282](https://github.com/redimp/otterwiki/pull/282).

### Code Refactoring

- PageIndex uses PageIndexEntry dataclass ([b57a5b6](https://github.com/redimp/otterwiki/commit/b57a5b63b1591a47b82c66ed60b67f6e7948295e)).
- PageIndex moved into pageindex.py ([94421e1](https://github.com/redimp/otterwiki/commit/94421e190c12d5c7e35e12bfa5c909b7860e59c0)).
- PageIndex.render() extracted meta_description() ([d4f858a](https://github.com/redimp/otterwiki/commit/d4f858a24255ea2eebe7de56cf03b99b299cbf5a)).

## [v2.13.0](https://github.com/redimp/otterwiki/releases/tag/v2.13.0) - 2025-08-02

<small>[Compare with v2.12.0](https://github.com/redimp/otterwiki/compare/v2.12.0...v2.13.0)</small>

### Features

- added editor shortcuts: bold, italic, link, insert/format table, mostly done
  by Dan Falcone @dafalcon, see [PR#251](https://github.com/redimp/otterwiki/pull/251)
- enabled spellchecking (via the browser) in the editor ([0a7e44a](https://github.com/redimp/otterwiki/commit/0a7e44a668e4c9fbda25f985c0c7b853ec85f1e7)).
- url pasting: When pasting an url on a selected word, the url is pasted
  as markdown link `[word](https://pasted.url)`. See #259.
- url button (and shortcut): If a text has been selected when the button
  is pressed, a markdown link is inserted. The selected text becomes the
  description and the cursor is placed so that the url can be entered.
  ([379799](https://github.com/redimp/otterwiki/commit/add643344a7cbf6401c6ef0d1ef4d745e2379799)).
  This was discussed in #251.

### Bug Fixes

- typo in PGID check ([a5bbeba](https://github.com/redimp/otterwiki/commit/a5bbeba1b666c804de81094c5c3181877553f160)).

## [v2.12.0](https://github.com/redimp/otterwiki/releases/tag/v2.12.0) - 2025-07-20

<small>[Compare with v2.11.1](https://github.com/redimp/otterwiki/compare/v2.11.1...v2.12.0)</small>

### Features

- handle `.md` suffix in URLs, pointing to Pages, see #267 ([a924afe](https://github.com/redimp/otterwiki/commit/a924afeafd6afbd7ff9a76cc16b7e7d4e333a20d)).
- improved the `<head> <meta og:...>` tags: site name and descriptions based upon the pages content ([d10eea8](https://github.com/redimp/otterwiki/commit/d10eea8289614fa731a521d54fa8ff57159dc00b)).
- added `SITE_LANG` to configure the lang attribute of the html element ([3d897a4](https://github.com/redimp/otterwiki/commit/3d897a42102f9efe183757d538e4010a423ff690)).

### Bug Fixes

- handle existing `PUID` and `PGIDs` so that containers can restart, see #257 ([ec9a3c6](https://github.com/redimp/otterwiki/commit/ec9a3c6ca9c123f34dce3b5abb5a2035ccba52ff)).
- set the `download_name` when an attachment is requested by revision, see #260 ([e20de72](https://github.com/redimp/otterwiki/commit/e20de72028a38784d75768c4e6f32b2093f19982)).
- default mimetype set to octet-stream, see #260 ([4eca70f](https://github.com/redimp/otterwiki/commit/4eca70ff3a6c2f12bd62121311233a816949487d)).
- increased proxy read/send timeout for nginx, see #254 ([5d35f4a](https://github.com/redimp/otterwiki/commit/5d35f4a9d221a0c6a40dd4fc38993210c5428ce8)).

## [v2.11.1](https://github.com/redimp/otterwiki/releases/tag/v2.11.1) - 2025-06-26

<small>[Compare with v2.11.0](https://github.com/redimp/otterwiki/compare/v2.11.0...v2.11.1)</small>

### Bug Fixes

- markdown files are no longer listed as attachments, see #254. ([514417a](https://github.com/redimp/otterwiki/commit/514417a09be37efc0eeace25a534398dbc61d761)).
- Dockerfile use ENV not ARG for PUID and PGID ([438b4ac](https://github.com/redimp/otterwiki/commit/438b4accd62c75ef9ddaf45295bcbf69b335acf4)).
- workaround for unraid templates with PGID=100, see #257 ([d27f993](https://github.com/redimp/otterwiki/commit/d27f993daf57134ac3e94b2deed8af1a8d51b91e)).

## [v2.11.0](https://github.com/redimp/otterwiki/releases/tag/v2.11.0) - 2025-06-22

<small>[Compare with v2.10.6](https://github.com/redimp/otterwiki/compare/v2.10.6...v2.11.0)</small>

### Features

- added `SIDEBAR_MENUTREE_FOCUS` setting that allows to always display all pages in the sidebar, see #169 ([495cca1](https://github.com/redimp/otterwiki/commit/495cca13432f2a9cc334be6fd0055e598857fbcd)).
- added rss/atom feeds of the changelog, see #255 ([8f53031](https://github.com/redimp/otterwiki/commit/8f5303168662c08fdc5c593958bfb75d147f2ba8)).
- enable fragments in wikilinks, e.g. `[[wikilinks#fragment]]`, see #246 ([f60f6e9](https://github.com/redimp/otterwiki/commit/f60f6e900c5af981a144a43375eef301ea9a8850)).
- the docker -slim image can handle --user to change the uid/gid, see #252 ([f32fd07](https://github.com/redimp/otterwiki/commit/f32fd07388eaf7cd81b3f1654eca38b6c22f1ba8)).
- docker image: www-data uid/gid is set to PUID/PGID, see #252 ([a46520a](https://github.com/redimp/otterwiki/commit/a46520a79e143445b17f9b25fba3eae40bad24dc)).

### Bug Fixes

- Unicode characters breaking page history, see #253 ([3640ccf](https://github.com/redimp/otterwiki/commit/3640ccfa23471b6428224c865efb69ab56fb664f)).

### Code Refactoring

- followed pyright suggestions, cleaned up ([e24f648](https://github.com/redimp/otterwiki/commit/e24f648045e5a0052be652dc2bbbfdf03be8c881)).

## [v2.10.6](https://github.com/redimp/otterwiki/releases/tag/v2.10.6) - 2025-04-28

<small>[Compare with v2.10.5](https://github.com/redimp/otterwiki/compare/v2.10.5...v2.10.6)</small>

### Deployment Features

- added curl to the Docker images for health checks, see #242 ([f311403](https://github.com/redimp/otterwiki/commit/f3114034cab94db1aa09e937d981dce607fcdbe8)).

### Bug Fixes

- titleSs() handles now ß at the end of the page correct, see #243 ([d71e8f1](https://github.com/redimp/otterwiki/commit/d71e8f125d8491d99ab6d1243098163fd2651e06)).
- commits and diffs of filenames with quotes can be rendered, see #244 ([fedfd48](https://github.com/redimp/otterwiki/commit/fedfd485b1a32f486d4cf00fa60017ae178ebe78)).

## [v2.10.5](https://github.com/redimp/otterwiki/releases/tag/v2.10.5) - 2025-04-16

<small>[Compare with v2.10.4](https://github.com/redimp/otterwiki/compare/v2.10.4...v2.10.5)</small>

### Chores

Usually chores are not part of the changelog, here an exception is made:

- with [PR233](https://github.com/redimp/otterwiki/pull/233) a pile pf type
  hints have been introduced into An Otter Wiki which increases the code quality
  and should help with further development.

### Features

- yaml frontmatter renderer plugin added see [PR#207](https://github.com/redimp/otterwiki/pull/207) by @ReessKennedy.
- check if registered name is looks sane, to prevent spam. See #235 ([778fc4f](https://github.com/redimp/otterwiki/commit/778fc4f2fd703509548a2097a14059d147779c9d)).

### Bug Fixes

- Fixed line spacing in the editor. Set `pre margin-bottom` only when viewing ([8a3a6ed](https://github.com/redimp/otterwiki/commit/8a3a6ed0590ffd08f481c7f3ee3ae0ea83844985)).
- `/<Pagename>/blame` links to the "view" endpoint which uses `?revision=`, see #230 ([40ee3bf](https://github.com/redimp/otterwiki/commit/40ee3bfae9f0c2543a4ec6c7d8761d281a8a6159)).
- correct date headers for attachments, see #231 and #232 ([5dbccf](https://github.com/redimp/otterwiki/pull/232/commits/5dbccfdf8e35b5037e974deda0b805168fc3face)).
- docker: bumped up the uwsgi buffer size, see #184 ([ae4d3aa](https://github.com/redimp/otterwiki/commit/ae4d3aad688a1cb04ff8d5c89983aad3d629bbb5)).
- Disable hotkeys <kbd>[</kbd> and <kbd>/</kbd> when modifiers are enabled by @dafalcon, see #236 ([1359032](https://github.com/redimp/otterwiki/commit/13590322e312a47094589f1bebecdba8e0c4d174)).

### Dependencies

- updated mermaid to 11.6.0 ([f3b38be](https://github.com/redimp/otterwiki/commit/f3b38be2c1775a8f8c3bd1672acbeb62a6be8f65)).

## [v2.10.4](https://github.com/redimp/otterwiki/releases/tag/v2.10.4) - 2025-03-28

<small>[Compare with v2.10.3](https://github.com/redimp/otterwiki/compare/v2.10.3...v2.10.4)</small>

### Bug Fixes

- Anther c hotkey related fix: disable hotkey on mobile browsers [PR#227](https://github.com/redimp/otterwiki/pull/227)

## [v2.10.3](https://github.com/redimp/otterwiki/releases/tag/v2.10.3) - 2025-03-26

<small>[Compare with v2.10.2](https://github.com/redimp/otterwiki/compare/v2.10.2...v2.10.3)</small>

### Bug Fixes

- the hotkey c (for create page) must not prevent Ctrl-C or CMD-C ([60d13fb](https://github.com/redimp/otterwiki/commit/60d13fb1dce4460628f491fcce5624e74a813a8c)).

## [v2.10.2](https://github.com/redimp/otterwiki/releases/tag/v2.10.2) - 2025-03-25

<small>[Compare with v2.10.1](https://github.com/redimp/otterwiki/compare/v2.10.1...v2.10.2)</small>

### Features

- keyboard shortcuts for edit, create, toggle sidebar, save and toggle preview
  by Dan Falcone @dafalcon, see [PR#224](https://github.com/redimp/otterwiki/pull/224)
- editor buttons reorganized, by Thierry Trafelet @ttrafelet([d8cc33a](https://github.com/redimp/otterwiki/commit/d8cc33a3d6e3ba3dc4f9c6d82a36bbfd6c8cd387))

## [v2.10.1](https://github.com/redimp/otterwiki/releases/tag/v2.10.1) - 2025-03-13

<small>[Compare with v2.10.0](https://github.com/redimp/otterwiki/compare/v2.10.0...v2.10.1)</small>

### Bug Fixes

- `<TAB>` now inserts softtabs (4 spaces) and indents when lines are selected, see #196. ([3d6d4d5](https://github.com/redimp/otterwiki/commit/3d6d4d54eece42a43a4540f40f3e415ab78deb69)).
- Handle empty fancy- or folded blocks correct. ([29a6b2d](https://github.com/redimp/otterwiki/commit/29a6b2df1f33968a5695c50d8359cd78d7636425)).

### Documentation

- Improved the Documentation of nested lists, see #196. ([cd47a41](https://github.com/redimp/otterwiki/commit/cd47a4113f2722984281c92c4bf93363c686b940))

## [v2.10.0](https://github.com/redimp/otterwiki/releases/tag/v2.10.0) - 2025-03-09

<small>[Compare with v2.9.4](https://github.com/redimp/otterwiki/compare/v2.9.4...v2.10.0)</small>

### Features

- Extend menu buttons with (some) missing functionality (alerts, panels, quote,
  spoiler, expand etc.), by Thierry Trafelet @ttrafelet see [#202](https://github.com/redimp/otterwiki/pull/202)

### Bug Fixes

- fix: rendering of lists (etc) in fancy-, alert-, spoiler- and folded blocks,
  see #214 ([11cdf82](https://github.com/redimp/otterwiki/commit/11cdf821c0a7dde9140d4e7b8102e0c96f2236ba)).
- tweaking the alert blocks, so that light and dark mode match, see #213 ([76ad321](https://github.com/redimp/otterwiki/commit/76ad321fc7d63c832e6067e744dcdc7fc5481e8b)).
- make sure no extra newlines are added to pre formatted blocks, see #212 ([518d9f0](https://github.com/redimp/otterwiki/commit/518d9f0be889cde90c0a88f6a7307fde3c4b7ae9)).
- remove the "copy-to-clipboard" block from syntax documentation, see #212 ([2316bc9](https://github.com/redimp/otterwiki/commit/2316bc9f560104beeb1392c82b973b2d72718598)).
- correct spacing in div.page-wrapper layout.html, see #212 ([0e8011b](https://github.com/redimp/otterwiki/commit/0e8011bb63227b8a75f29a3e80fc6e31f1304953)).
- Named footnotes not linking correctly, see #211 ([bdabb71](https://github.com/redimp/otterwiki/commit/bdabb712118cf5b49065c3a4bf819a9a361382b5)).
- use full path for pages when displaying single commits, see #209 ([5ade21c](https://github.com/redimp/otterwiki/commit/5ade21c26bc3e4b37b0d7258880e315390fda416)).
- handle `FileNotFoundError` on updating the ftoc cache ([6bfe892](https://github.com/redimp/otterwiki/commit/6bfe8923a7f17c94606dacefc66bbb818a49ed9a)).
- typo in the `MAX_FORM_MEMORY_SIZE variable`  ([0d5eab5](https://github.com/redimp/otterwiki/commit/0d5eab5ec2305a574c198bdb1b80220e66db6f11)).

### Docs

- added documentation about how to indent items in nested lists, see #196 ([131644d](https://github.com/redimp/otterwiki/commit/131644db87ecb16ca3a07ed37da14486e63e3f60))

## [v2.9.4](https://github.com/redimp/otterwiki/releases/tag/v2.9.4) - 2025-02-27

<small>[Compare with v2.9.3](https://github.com/redimp/otterwiki/compare/v2.9.3...v2.9.4)</small>

### Bug Fixes

- use full path for pages when displaying single commits, see #209 ([0bdd563](https://github.com/redimp/otterwiki/commit/0bdd5634491db2ef3fc17031c33b719c46e003d1)).
- handle FileNotFoundError on updating the ftoc cache ([2e6c502](https://github.com/redimp/otterwiki/commit/2e6c50287cc8f2105d332f08863caac3d3f413aa)).
- don't strip whitespace from code blocks #206 ([680f74a](https://github.com/redimp/otterwiki/commit/680f74a8ad30f02653f3dd473d3bc7c400e853aa)).

## [v2.9.3](https://github.com/redimp/otterwiki/releases/tag/v2.9.3) - 2025-02-12

<small>[Compare with v2.9.2](https://github.com/redimp/otterwiki/compare/v2.9.2...v2.9.3)</small>

### Bug Fixes

- Users with empty (or None) password hashes can try to login and recover their passwords, see #204 and #205 ([bd594fa](https://github.com/redimp/otterwiki/commit/bd594faa12c1ff2663697b58a4e8fe051dc4af2e)).
- Page blame for a page where the file has trailing new lines, see #200 ([ffefcad](https://github.com/redimp/otterwiki/commit/ffefcadadb199e979d5d4f06355dbc3526821eb6)).

## [v2.9.2](https://github.com/redimp/otterwiki/releases/tag/v2.9.2) - 2025-01-31

<small>[Compare with v2.9.1](https://github.com/redimp/otterwiki/compare/v2.9.1...v2.9.2)</small>

### Bug Fixes

- With `RETAIN_PAGE_NAME_CASE` enabled only the capitalization of the filename determines the captialization of the Page name, see #193 ([83dd439](https://github.com/redimp/otterwiki/commit/83dd4395d12802a773ffbe0f1d08e0fa1527b669)).
- cursormagicword back to just characters, see #167 ([f930d44](https://github.com/redimp/otterwiki/commit/f930d44cf4759f93820cdc79299a3b04cb3d058b)).
- saving application preferences does not change content and editing preferences anymore, see #192 ([5b76af3](https://github.com/redimp/otterwiki/commit/5b76af35d12dd7b4cc3b4e110ab765f4c3bc2cae)).

## [v2.9.1](https://github.com/redimp/otterwiki/releases/tag/v2.9.1) - 2025-01-26

<small>[Compare with v2.9.0](https://github.com/redimp/otterwiki/compare/v2.9.0...v2.9.1)</small>

### Bug Fixes

- added setting `MAX_FORM_MEMORY_SIZE`, see #179 ([95d661e](https://github.com/redimp/otterwiki/commit/95d661e5b34d0f104b27b3e08572c7e50ec58c7b)).
- in `pygments_render` replace [] with numeric codes, see #190 ([666cfd0](https://github.com/redimp/otterwiki/commit/666cfd004175023afd493c5c86a3a37d30786d6a)).

## [v2.9.0](https://github.com/redimp/otterwiki/releases/tag/v2.9.0) - 2025-01-23

<small>[Compare with v2.8.0](https://github.com/redimp/otterwiki/compare/v2.8.0...v2.9.0)</small>

### Features

- added optional caseless sorting of the sidebar ([47aefc0](https://github.com/redimp/otterwiki/commit/47aefc012d5cac58f63ac35c7726902bb1596ee6) and [#187](https://github.com/redimp/otterwiki/pull/187) by [rhartmann](https://github.com/rhartmann).
- added some responsiveness to the sidebar, see #185 ([a69f514](https://github.com/redimp/otterwiki/commit/a69f514d51ae84981f7537bc1111250c55c733e2)).
- PageIndex uses `get_ftoc` for cached ftocs to reduce load time, see #183 ([ea24cd0](https://github.com/redimp/otterwiki/commit/ea24cd07139bdddbf019a3e3aa9a457167143b4c)).
- added option to add line numbers to code blocks, see #176 ([76d13c2](https://github.com/redimp/otterwiki/commit/76d13c2a81994b18977a688f46d884d7c2e30a00)).
- print otterwiki, nginx and supervisord versions, see #188 ([0d49d1b](https://github.com/redimp/otterwiki/commit/0d49d1b41d19c80236c1e405d5c3b8cc8c487e0c)).

### Bug Fixes

- preview of a paragaph with `_italic_` markup, see #167 ([c364efb](https://github.com/redimp/otterwiki/commit/c364efb60518833a1236492c8b6634a94d2dec5e)).
- word-break n the sidebar optimized. Do not break the `::before` element, see #169 ([ecfe061](https://github.com/redimp/otterwiki/commit/ecfe061e46131fe7f0ae924621cdb40276188aac)).

### Code Refactoring

- anonoymous users drafts are now stored in the database ([091a9e7](https://github.com/redimp/otterwiki/commit/091a9e7c933ffa26f1b59e7e0e2ee3582b6c7bd9)).
- An `anonymous_user` has now a uid stored in the session ([1ebeb8d](https://github.com/redimp/otterwiki/commit/1ebeb8d3eae39c05b36f5929c10482480ce2bef5)).

## [v2.8.0](https://github.com/redimp/otterwiki/releases/tag/v2.8.0) - 2024-11-17

<small>[Compare with v2.7.0](https://github.com/redimp/otterwiki/compare/v2.7.0...v2.8.0)</small>

### Features

- added a convenient way to add attachments and wikilinks, this implements #128. ([fa34e02](https://github.com/redimp/otterwiki/commit/fa34e028a9a4c1f16536f3ca6bf46ab97c81d3d7))
- attachments can not be linked relative to the page, e.g. `![](./example.png)`,
  this implements #163. ([3170c64](https://github.com/redimp/otterwiki/commit/3170c64cd66c931380a82029ed6f0986521cf636))
- the editor makes use of this feature and adds pasted images using relative links. ([1945f2e](https://github.com/redimp/otterwiki/commit/1945f2e5ed537a9eb20e3e593bbf822b0e9b27c0))
- allow renaming of folders and to remove a page without removing the
  attachments and sub-pages, this implements #149 and $150. ([e7d92be](https://github.com/redimp/otterwiki/commit/e7d92bee553dc31f7fcd6a60f5523d90b4d040c5))
- new config option: `WIKILINK_STYLE` allows rendering Wikilinks in a compability mode.
  This implements #155. ([067668f](https://github.com/redimp/otterwiki/commit/067668fac9f9b255b0f2057926a477eabeeabc2a))

### Dependencies

- updated mermaid to 11.4.0 this fixes #164. ([d6c10d5](https://github.com/redimp/otterwiki/commit/d6c10d502278cc6f395b6359ca4a1dd8ea8570b4))
- updated python dependencies ([2207643](https://github.com/redimp/otterwiki/commit/2207643ae3090d73eed471544e08bd93848da408))
  - Werkzeug 3.1.3
  - Flask 3.1.0
  - Flask-Mail 0.10.0
  - cython 3.0.11

### Bug Fixes

- enable renaming of folders without markdown file ([bfd6615](https://github.com/redimp/otterwiki/commit/bfd6615880d3d1cc208fa939a7cf746ea0f59945)).

### Code Refactoring

- moved helper methods into `helpers.py` ([a921cb8](https://github.com/redimp/otterwiki/commit/a921cb895c0429b14212f4be7b9103070f0fc960)).
- User Model moved into `otterwiki.models` ([e9d6cbe](https://github.com/redimp/otterwiki/commit/e9d6cbe4e434e38a1d7021565ae3e365d5215558)).

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
- Part of the release are slim images, built with only uWSGI, without nginx and supervisord based on alpine 3.20.1. Running as unprivileged user, listening on port 8080. docker image tags get -slim appended e.g. `redimp/otterwiki:2.4.4-slim` [#121](https://github.com/redimp/otterwiki/issues/121)

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

<!-- vim: set tw=0 nowrap: -->
