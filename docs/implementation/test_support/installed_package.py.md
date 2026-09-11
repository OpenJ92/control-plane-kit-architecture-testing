Source: [test_support/installed_package.py](../../../test_support/installed_package.py).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

This executable installation check imports the installed package, compares version and explicit exports, checks distribution metadata for no runtime dependencies, and rejects an import root containing the selected /tmp/package build path. test.sh supplies the outside-source working directory and isolated installation. The path check is a specific packaging assertion, not a universal provenance detector for every possible checkout location. Preserve the coordinated __all__/version expectations when public owners change; this helper does not test every exported behavior or establish consumer compatibility.
