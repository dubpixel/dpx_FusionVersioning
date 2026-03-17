# DPX Fusion Versioning - Project Context

## Purpose
This project is an Autodesk Fusion 360 add-in that keeps naming and file versions synchronized.

It does two main things:
1. Version-tags matching components and bodies using the Fusion document version + 1.
2. Optionally exports matching items to STL files after versioning.

Matching is based on a filename-derived prefix and naming conventions.

## Current Version
- Add-in version: 1.2.0
- Manifest version: 1.2.0

## Core Behavior
When the command runs:
1. Validates there is an active saved Fusion design (`doc.dataFile` must exist).
2. Reads current file version and computes `nextVerNum = current + 1`.
3. Builds prefix from filename as first 3 letters + underscore (`abc_`).
4. Renames matching components (excluding root component).
5. Renames matching bodies in all components and root component.
6. Saves document with default or user-supplied comment.
7. If using export command, exports selected tagged items as STL.

## Prefix and Version Matching Rules
- Prefix source: first 3 letters of filename + `_`.
- Prefix matching supports both `_` and `-` separators.
  - Example: `dpx_widget` matches `dpx_`
  - Example: `dpx-widget` also matches `dpx_`
- Existing version suffix detection uses regex:
  - `^(.+)_v(\d+)$`
- Only a trailing `_v` + digits is treated as a version suffix.
- Names like `dpx_vertical_mount` are preserved correctly.

## Commands Added to Fusion UI
Two buttons are registered in the Modify panel (`SolidModifyPanel`) of the solid workspace (`FusionSolidEnvironment`):
- DPX Versioning
- DPX Version + Export

Both buttons share the same versioning path.
The second button additionally runs STL export logic.

## Main File Map
- `dpxVersioning.py`
  - Add-in entry points (`run`, `stop`)
  - Command handlers
  - Versioning logic
  - Export logic
- `dpxVersioning.manifest`
  - Fusion add-in metadata, startup behavior, OS support, version
- `install_addin.sh`
  - macOS copy installer (cp)
- `install_addin_rsync.sh`
  - macOS copy installer (rsync)
- `install_addin.bat`
  - Windows installer (xcopy)
- `CHANGELOG.md`
  - Task-oriented change history and bug-fix notes

## Architectural Notes (Fusion API)
- Event handlers are appended to global `handlers` list to prevent garbage collection.
- Root component cannot be renamed in Fusion and is explicitly skipped.
- Design traversal uses:
  - `design.allComponents` for components
  - `comp.bRepBodies` and `rootComp.bRepBodies` for bodies
- Export uses `design.exportManager` and STL export options.

## Export Logic Summary
- Collect tagged components and tagged bodies.
- Exclude tagged bodies whose parent component is tagged (to avoid duplicate exports under parent export).
- Ask user for destination folder.
- For each export item:
  - Temporarily force visibility needed for intended export composition.
  - Hide tagged nested items so they can be exported separately.
  - Export to `{item_name}.stl`.
  - Restore visibility.
- Show completion summary and failures.

## Known Constraints and Risks
- Body names are not globally unique in all assemblies; duplicate item names can overwrite STL files.
- Visibility restore is best-effort and may skip deleted/invalid entities.
- Prefix logic is intentionally strict to 3-letter convention; non-conforming filenames may miss targets.
- Save is required for version sync; unsaved documents are blocked.

## Safe Change Areas
Low-risk edits:
- UI text and message boxes.
- Commit message format.
- Export preview formatting.
- Filename sanitization for export output.

Medium-risk edits:
- Prefix derivation strategy.
- Visibility handling in export composition.
- Regex behavior for version stripping.

High-risk edits:
- Event wiring and handler lifetime management.
- Fusion object traversal assumptions.
- Root component logic and save flow sequencing.

## Suggested Near-Term Improvements
1. Ensure unique STL filenames (append index or occurrence path).
2. Add optional dry-run mode (rename preview without save).
3. Add opt-in body renaming toggle in command inputs.
4. Improve installer scripts to replace existing add-in dir atomically.
5. Add structured debug logging switch instead of commented debug blocks.

## Quick Verification Checklist
1. Add-in loads and both commands appear in Modify panel.
2. Unsaved document shows expected warning.
3. Tagged components and bodies get `_v{next}` suffix.
4. Root component is never renamed.
5. Document saves successfully after rename.
6. Export command writes STL files to selected folder.
7. Visibility is restored after export.
