
## Unresolved Issue: GFF Parsing Limitation

During the investigation of displaying all features from `no_sequence.gff`, it was discovered that the `BCBio.GFF.parse` function, which `DnaFeaturesViewer` relies on for GFF parsing, appears to be a bottleneck.

**The Problem:**
`BCBio.GFF.parse` consistently returns only the first top-level record from a GFF file, even when the file contains multiple distinct features (e.g., gene, exons, CDS, TF_binding_site). This prevents `DnaFeaturesViewer` from loading and subsequently displaying all features present in the GFF file.

**Impact:**
Despite efforts to adjust plotting parameters (like `figure_width`, `figure_height`, `feature_level_height`), and even attempting to make the encompassing "gene" feature transparent or an outline, the smaller, nested features were never visible in the generated graphics. This is because they were not being loaded into the `GraphicRecord` object in the first place due to the parsing limitation.

**Proposed Solution (Requires Further Investigation/Development):**
To fully resolve this, `DnaFeaturesViewer` would need to:
1.  **Adopt an alternative GFF parsing strategy:** This might involve using a different Python library for GFF parsing that can reliably extract all features from a multi-feature GFF file.
2.  **Implement a custom GFF parser:** Develop a parser within `DnaFeaturesViewer` that can correctly handle the structure of GFF files and extract all features.

This issue highlights a fundamental limitation in the current GFF parsing mechanism within `DnaFeaturesViewer` for files containing multiple features that are not nested under a single, primary record in a way that `BCBio.GFF.parse` fully interprets.
