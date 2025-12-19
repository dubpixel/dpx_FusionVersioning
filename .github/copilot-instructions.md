# DPX Fusion Versioning - Agent Instructions

## Project Overview

**Repository:** `dpx_FusionVersioning`  
**Type:** Fusion 360 Add-In (Python)  
**Purpose:** Automated version tagging for components and bodies in Fusion 360 designs

---

## Goals

**Primary Goal:** Keep Fusion 360 component and body names synchronized with file version numbers.

**The Problem It Solves:** When iterating on a Fusion 360 design, the file version increments (v1, v2, v3...), but components and bodies have no indication of which version they belong to. This makes it hard to track what's current, especially when exporting or referencing parts.

---

## Features

- **Prefix Detection:** Automatically extracts filename prefix (first 3 characters + underscore)
- **Selective Tagging:** Only tags components/bodies that match the file's naming convention
- **Version Sync:** Uses `file version + 1` to stay synchronized after save
- **Separator Support:** Handles both underscore (`_`) and dash (`-`) separators
- **Smart Tag Replacement:** Replaces existing `_v#` tags (only matches `_v` followed by digits at end)
- **Auto-Save:** Saves after renaming to maintain version sync
- **Root Component Safety:** Skips root component (Fusion doesn't allow renaming it)

---

## Workflow

1. User clicks "DPX Versioning" button in the Modify panel
2. Script extracts prefix from filename (e.g., `dpx_widget.f3d` → `dpx_`)
3. Finds all components and bodies starting with that prefix
4. Renames them with next version number (current version + 1)
5. Prompts for optional commit message
6. Saves the file so versions stay in sync

---

## Examples

**Before:**
- File: `dpx_widget.f3d` (version 3)
- Components: `dpx_lever`, `dpx_bracket_v2`, `dpx_vertical_mount`
- Bodies: `dpx_base`, `std_screw`

**After running DPX Versioning:**
- Components: `dpx_lever_v4`, `dpx_bracket_v4`, `dpx_vertical_mount_v4`
- Bodies: `dpx_base_v4`, `std_screw` (unchanged - wrong prefix)
- File saves and becomes version 4

---

## Technical Notes

### Version Tag Pattern
The regex `^(.+)_v(\d+)$` is used to strip existing version tags:
- Matches `_v` followed by **digits only** at the **end** of the name
- `dpx_lever_v7` → base name: `dpx_lever` ✓
- `dpx_vertical_mount` → base name: `dpx_vertical_mount` ✓ (no version tag)
- `dpx_valve_v12` → base name: `dpx_valve` ✓

### Root Component
- Fusion 360 does not allow renaming the root component
- The script explicitly skips `design.rootComponent`
- Bodies inside the root component CAN be renamed

### Event Handler Pattern
- All event handlers stored in global `handlers` list
- Prevents garbage collection during execution
- Standard Fusion 360 add-in pattern

---

## File Structure

```
dpx_FusionVersioning/
├── dpxVersioning.py          # Main add-in code
├── dpxVersioning.manifest    # Fusion 360 manifest
├── CHANGELOG.md              # Version history
├── README.md                 # User documentation
├── resources/                # Icons (16x16, 32x32 PNG)
└── .github/
    └── copilot-instructions.md  # AI coding guidelines
```

---

## AI Development Guidelines

### Ground Rules
- No modifications to working code without explicit request
- Comprehensive commenting and preservation of existing comments
- Small, incremental changes to maintain stability
- Stay focused on current task - don't jump ahead
- Document all changes in CHANGELOG.md (not in .py file)

### Fusion 360 Specifics
- Always use `adsk.core.Application.get()` to access the app
- Keep event handlers in global list to prevent GC
- Wrap operations in try-except with `ui.messageBox()` for errors
- Check for active design/document before operations
- Use `doc.save(commitMessage)` for version control integration

### Code Patterns
```python
# Get active design
design = adsk.fusion.Design.cast(app.activeProduct)

# Iterate components (skip root)
for comp in design.allComponents:
    if comp == design.rootComponent:
        continue
    # process component...

# Access bodies
for body in comp.bRepBodies:
    # process body...

# Version tag regex (matches _v followed by digits at END only)
match = re.match(r'^(.+)_v(\d+)$', name)
baseName = match.group(1) if match else name
```

---

## Future Considerations

- `rename_bodies` flag exists for potential toggle (currently always True)
- Could add UI options for prefix customization
- Could support batch processing multiple files
- Could add undo functionality