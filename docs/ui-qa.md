# UI quality assurance

For Options Flow changes verify both German and English on iPhone-width and desktop-width layouts:

- every root menu item opens and submits
- the six-item sensor selector serializes normally
- group labels remain one line: Device · App · last access
- known access times sort oldest first; unknown times appear last
- named playback blockers do not erase other submitted switches
- explicit group Back navigation preserves the draft
- Review changes is absent at zero semantic changes
- no empty bullet or placeholder-only review form appears

Visual checks complement, but do not replace, flow serialization, registry, state-machine, reload, and restoration tests.
