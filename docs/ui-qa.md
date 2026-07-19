# UI quality assurance

Changes to the options flow should be checked with the standard Home Assistant frontend on iPhone, iPad, and desktop.

Verify:

- root-menu labels and descriptions
- all six sensor switches in both languages
- draft-only navigation and final apply
- two-line player labels without horizontal overflow
- automatic-cleanup placeholders, including the dynamic age threshold
- manual-cleanup age-independence wording
- confirmation pages and inline errors
- dark-theme readability without integration-specific CSS

EMBi uses native Home Assistant selectors and does not inject frontend styling.
