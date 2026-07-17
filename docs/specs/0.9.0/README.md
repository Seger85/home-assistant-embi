# EMBi 0.9.0 – Frozen Product, UX and Release Contract

Status: **frozen**  
Target release: **0.9.0 stable**

This directory is the authoritative specification for EMBi 0.9.0. It replaces chat context as the implementation source of truth.

## Authority order

1. `requirements.yaml`
2. `00-master-specification.md`
3. the relevant domain specification
4. the final UI-copy files
5. `10-test-and-acceptance-matrix.md`
6. existing repository documentation

A real contradiction is a blocker. Do not invent a product decision.

## Release rule

The implementation is complete only when every blocker requirement has implementation evidence, automated tests, required live verification, required visual verification and a passing release contract.

No development version, release candidate or prerelease is published. A pull-request artifact may be used for private acceptance without a public tag or release.
