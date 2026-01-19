# Scribe's Journal

## 2024-10-24 - Future-Proofing Documentation vs Reality
**Learning:** The project documentation lists unreleased AI models (e.g., `gpt-5`, `gpt-4.1`) as valid configuration options. While the code contains logic to handle these identifiers (likely for future compatibility), stating them as current features in `README.md` is misleading.
**Action:** When documenting model options, strictly separate "Available Now" from "Planned/Experimental". Validate that listed models are actually accepted by the provider APIs to avoid runtime errors for users following the docs.
