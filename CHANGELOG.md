# Changelog

All notable changes to DPX Fusion Versioning are documented here.

Format: User prompt as single line, followed by itemized solution with → bullet.

---

## [2.4.3] - 2026-09-05

**move "Rename untagged body" to a top-level toggle, default off**

→ Moved out of the "Tagged Components" group entirely — now a standalone panel option above it, near "Detected prefix"  
→ Default flipped from on to off (`RENAME_SOLE_UNTAGGED_BODY = False`) — the sole-untagged-body edge case now exports under the component's name without touching the document body unless explicitly enabled  

---

## [2.4.2] - 2026-09-05

**export panel polish: shorter label, moved checkbox**

→ "Rename untagged body to match component (in document)" shortened to "Rename untagged body"  
→ Moved out of its own "Options" group into the top of "Tagged Components" — it's a component-scoped setting, so it lives with the group it affects  

---

## [2.4.0] - 2026-09-05

**settingize the sole-untagged-body in-document rename**

→ Added an "Options" group to the export panel with "Rename untagged body to match component (in document)" (default: on)  
→ When off, the sole-untagged-body edge case still exports under the component's name, but the body's actual name in the document is left untouched  
→ New `RENAME_SOLE_UNTAGGED_BODY` module constant is the fallback default for the legacy (no-panel) export path  

---

## [2.3.2] - 2026-09-05

**default Tagged Components checkboxes to unchecked**

→ Bodies are the common case; components stay available but no longer preselected — Tagged Bodies group is unaffected, still default-checked  

---

## [2.3.1] - 2026-09-05

**fix: tagged components silently dropped from export list**

→ Component dedup in `_collect_export_items` used `id(comp)` — a Python memory address that Fusion API proxy objects can recycle mid-loop, causing an unrelated component to be wrongly treated as "already seen" and dropped  
→ Switched to `comp.entityToken`, which Fusion guarantees stable per component  

---

## [2.3.0] - 2026-09-05

**sole-untagged-body edge case + show detected prefix in export panel**

→ Export panel now shows a "Detected prefix" line at the top so it's obvious what's being matched before scanning the Components/Bodies lists  
→ Edge case: a tagged component whose subtree has zero tagged bodies but exactly one body total now gets that body auto-renamed to match the component and exported anyway, with a warning — previously reported as a hard failure ("no tagged bodies found")  
→ Ambiguous case (zero tagged bodies, multiple untagged bodies) still fails as before — no way to guess which one was meant  
→ Export summary now has a separate "Warnings" section alongside "Exported"/"Failed" so a successful-but-auto-corrected export isn't buried under failures  

---

## [2.2.0] - 2026-09-05

**export panel picks up tagged bodies nested inside tagged components, and multi-body components no longer produce junk _part files**

→ Split the export checklist into two independent groups: "Tagged Components" and "Tagged Bodies" — every tagged body now gets its own row regardless of whether its parent component is also tagged (previously excluded, which hid bodies you wanted to cherry-pick individually)  
→ Component export now walks the full occurrence subtree recursively, collecting only tagged bodies at any nesting depth — previously only bodies directly owned by that one component were found, so tagged bodies living inside a nested subcomponent were silently skipped  
→ Removed the `_partN.stl` / merge-STL fallback entirely: a tagged component with one tagged body exports as `{component_name}.stl`; with multiple tagged bodies, each exports individually under its own already-versioned name — no more leftover unmerged fragment files  
→ Checking a component and one of its own bodies individually is allowed and simply exports that body twice under different names; the two groups are independent selections, not mutually exclusive  

---

## [2.1.4] - 2026-07-05

**debug toggle checkbox in export panel sub-pane**

→ Added collapsed "Debug" group with a "Show debug popup" checkbox to the Version + Export command panel (default: unchecked)  
→ Execute handler now reads the runtime checkbox value when present; falls back to the `SHOW_DEBUG_POPUP` constant on the Version Only path  
→ Lets users opt into debug output per-run from the UI instead of editing code  

---

## [2.1.3] - 2026-07-05

**debug vomit still there - make it a variable/option**

→ Added `SHOW_DEBUG_POPUP` config flag in code (default `False`) to control debug dialog behavior  
→ Removed always-on debug popup during normal successful runs  
→ Debug popup now appears automatically only if user parameter `version` sync fails  
→ Keeps parameter failure diagnostics available without spamming every run  

---

## [2.1.2] - 2026-06-24

**user variable 'version' stopped working - not updating anymore**

→ Fixed parameter creation: changed from `createByReal()` to `createByString()` — Fusion user parameters use string expressions, not float values  
→ Added debug logging to `update_version_parameter()` — now logs success/failure to debug_info array  
→ Moved debug_info initialization before parameter update — allows parameter update to log diagnostic messages  
→ Temporarily enabled debug output dialog — shows parameter update status to diagnose issues  
→ Added error details to exception handler — failures now show specific error message instead of silent return False  
→ Root cause: Fusion 360 API expects user parameters to be created with string expressions ("4"), not numeric ValueInput objects  

---

## [2.1.1] - 2026-06-09

**parametric text call to versioning broke - need to write to user variable 'version' with current version**

→ Added `update_version_parameter()` function that creates or updates a numeric user parameter named 'version'  
→ Parameter value set to `nextVerNum` (current file version + 1) to match body/component version tags  
→ Called automatically during versioning workflow, before any renaming starts  
→ Provides workaround for Autodesk breaking direct parametric text access to file version  
→ Parametric text (sketch text) can now reference the 'version' user parameter instead of broken direct version call  
→ Non-fatal: if parameter update fails, versioning workflow continues normally  

---

## [2.0.14] - 2026-05-19

**refinement medium is like what i do with the 3dprintsetting**

→ Changed mesh refinement back to MeshRefinementMedium (from Low in v2.0.13)  
→ Matches user's 3D print settings and standard quality expectations  
→ Real fix was individual body export (not ObjectCollection), not the mesh refinement level  

---

## [2.0.13] - 2026-05-19

**same error message no more details [still getting Invalid geometry type (3)]**

→ Changed to export each body individually instead of using ObjectCollection - may avoid geometry type conflicts  
→ Changed mesh refinement from MeshRefinementMedium to MeshRefinementLow - simpler mesh generation may succeed where medium fails  
→ Single-body components export to final filename; multi-body components create separate _part0, _part1, etc. files  
→ Added per-body error reporting to identify which specific body fails  

---

## [2.0.12] - 2026-05-19

**does not work. are you using the filename you started with because the script selects, then versions up, then exports - if its looking for the old filename maybe thats why its failing**

→ Added validation checks: verify occurrence.isValid and body.isValid before attempting export  
→ Check for stale references after rename operation that might invalidate occurrence/body handles  
→ Skip invalid occurrences/bodies with descriptive error instead of attempting export  
→ Note: Names ARE refreshed post-rename (line ~227), but investigating if object references become stale  

---

## [2.0.11] - 2026-05-19

**all fail for now. but they export fine via the 3d print function / idk if you should do that [switch to 3D print]**

→ Reverted v2.0.10 change - restored body collection approach from v2.0.4  
→ Back to passing BRepBody or ObjectCollection to createSTLExportOptions (not Occurrence)  
→ Changed based on v2.0.4 note that "API expects `BRepBody` or `ObjectCollection` of bodies, not `Occurrence` objects"  
→ v2.0.10 experiment of passing occurrence directly was incorrect per API requirements  

---

## [2.0.10] - 2026-05-19

**no they did not [still getting error 3: Invalid geometry type]**

→ Reverted body collection approach - trying to pass occurrence directly to createSTLExportOptions()  
→ Removed manual body collection and ObjectCollection creation  
→ Let Fusion handle which bodies to export from the occurrence  
→ Note: This contradicts v2.0.4 fix but testing different approach to resolve "Invalid geometry type" error  

---

## [2.0.9] - 2026-05-19

**ok so it still doesnt work same error 3: - are u sure ur exporting the right part the tree. - the body not the component needs to be selected. idk**

→ Fixed "Invalid geometry type" error by using `occ.bRepBodies` instead of `comp.bRepBodies`  
→ Root cause: bodies must come from the placed occurrence instance, not the component definition  
→ Component = definition/template; Occurrence = placed instance with position/context in assembly  
→ ExportManager needs bodies from the actual instance in the assembly tree to capture correct geometry and transforms  

---

## [2.0.8] - 2026-05-19

**they export fine via the normal 3d print operation maybe ur overcomplicating it**

→ Removed overcomplicated geometry validation checks (isSolid, volume > 0, mesh body detection, face counting)  
→ Simplified to: collect all bodies, make visible, attempt export, capture real Fusion error if it fails  
→ Let Fusion's exportManager handle validation — if bodies export via 3D print, they're valid  
→ Wrapped export operations in try/except to surface actual Fusion error messages instead of pre-validation guesses  
→ Updated AGENTS.md with mandatory rule: version must be bumped for every code change  

---

## [2.0.7] - 2026-05-19

**it works sometimes but determines the geometry is invalid sometimes and wont output im not sure how and why**

→ Added geometry validation before attempting STL export — prevents intermittent silent failures  
→ For component bodies: validates `body.isSolid`, checks `body.volume > 0`, filters out surface bodies and zero-volume geometry  
→ For standalone bodies: validates solid status with early-exit and descriptive error ("surface body - not solid" or "zero volume - invalid geometry")  
→ Updated error messages to be more specific ("no valid solid bodies - check for surfaces or zero volume" instead of generic "no bodies to export")  
→ **Root cause**: Fusion's `exportMgr.execute()` returns False for surface bodies, degenerate geometry, and zero-volume shapes, but previous code attempted export without validation  

---

## [2.0.6] - 2026-03-17

**you need to save, so the version prints correctly on the file. then export i think**

→ Moved export call back to AFTER doc.save() instead of before — better user flow and file version is fully updated before export runs  
→ Dialog sequence now: versioning summary → commit message prompt → save + "Document saved!" → export preview/execution  
→ Previous order (export before save) was confusing and meant export dialogs appeared before "Document saved!" message  

---

## [2.0.5] - 2026-03-17

**it says no visible bodies to export**

→ Fixed body collection logic — now collects ALL bodies from component before visibility manipulation, not after  
→ Tagged bodies inside tagged components were already filtered out from separate export (first-pass logic), so they must be included in the component export  
→ Previous logic hid tagged bodies then collected only visible ones, resulting in zero bodies collected even when bodies existed  
→ New logic: collect all bodies from component, make them all visible for export, only hide tagged sub-components (which do get separate exports)  

---

## [2.0.4] - 2026-03-17

**fyi that still did not work**

→ Fixed component export by passing body/bodies to `createSTLExportOptions()` instead of occurrence — API expects `BRepBody` or `ObjectCollection` of bodies, not `Occurrence` objects  
→ For single body in component: pass the body directly  
→ For multiple bodies in component: create `ObjectCollection.create()` and add all visible bodies  
→ Added check for zero visible bodies and route to failed_items with descriptive message  

---

## [2.0.3] - 2026-03-17

**its not outputting STLS**

→ Fixed `exportMgr.execute()` return value never being checked — Fusion silently returns `False` on export failure; code was always incrementing `exported_count` regardless, producing phantom success counts with zero actual files written  
→ Both export branches (component via occurrence, standalone body) now check the return value and route `False` into `failed_items` with a descriptive message  
→ Moved `export_bodies()` call to run *before* `doc.save()` — saving after renaming can invalidate occurrence references, causing Fusion to silently reject exports; export now runs while all object references are still valid  

---

## [2.0.2] - 2026-03-17

**stls arent exporting when i have components even tho it says i am**

→ Fixed `export_bodies()` passing bare `Component` object to `createSTLExportOptions()` instead of the `Occurrence` — Fusion silently skips export when given the component definition rather than the placed instance  
→ Changed `createSTLExportOptions(comp)` to `createSTLExportOptions(occ)` so assembly context (position, visibility) is correctly captured during STL export  

---

## [2.0.0] - 2026-01-01

**RTG - first stable production release**

→ Marked as RTG (Ready To Go) — production-stable build  
→ `debug_info` collection retained internally but display is commented out by default for minimal-noise UX  
→ File and resource cleanup  

---

## [1.1.4] - 2025-12-28

**Export STL overhaul + debug mode + always-rename enforcement**

→ Rewrote `export_bodies()` to use `design.exportManager` + `createSTLExportOptions()` / `execute()` directly — replaced 3D Print command approach  
→ Added `ui.createFolderDialog()` so user picks the STL destination folder per-export  
→ Added `debug_info` array that logs per-item rename details (prefix, base name, match result) for diagnostics  
→ Removed skip-if-already-correct logic — names are now **always** set unconditionally to guarantee version sync  
→ Export visibility logic: tagged child items are hidden so they get their own export; untagged child items forced visible to be included in parent export  
→ Visibility state fully restored after each export item  

---

## [1.1.0] - 2025-12-19

**Export feature implementation**

→ Added `matches_prefix()` helper function for reusable prefix matching  
→ Implemented `export_bodies()` with 3D Print command integration  
→ Collects tagged components and bodies, respecting visibility rules  
→ Shows export preview with item list before proceeding  
→ Makes items visible, selects them, and executes 3D Print command  
→ Restores original visibility after export  
→ Shows summary of exported/failed items  
→ Updated copilot-instructions.md with export rules and visibility logic  

---

## [1.0.9] - 2025-12-19

**Two buttons instead of modifier keys**

→ Removed key detection code (Shift/E/W all conflicted with Fusion)  
→ Added second button "DPX Version + Export" to Modify panel  
→ Both buttons share same versioning logic via `with_export` parameter  
→ Handler classes now accept `with_export` flag to control export behavior  
→ Cleaner, more intuitive UX - no modifier keys needed  

---

## [1.0.8] - 2025-12-19

**is there any way to make modifiers happen when u run the script. like if i hold shift when i click on it, it runs with an export subroutine at the end.**

→ Added `is_shift_held()` function to detect Shift key on macOS (Quartz) and Windows (ctypes)  
→ Added `export_bodies()` placeholder function for future export functionality  
→ Modifier key check happens immediately on execute, before any dialogs  
→ SHIFT+Click now triggers export after versioning (placeholder message for now)  

---

## [1.0.7] - 2025-12-19

**Bug fixes for unsaved documents and shadowed import**

→ Added check for unsaved documents (`doc.dataFile` is None) with friendly message  
→ Removed duplicate `import re` inside function that was shadowing the global import  
→ Fixed `UnboundLocalError: cannot access local variable 're'`  

---

## [1.0.6] - 2025-12-18

**really it shouldnt just split at _v it should split at _v# - it will never not be _v# and it would eliminate issues with a filename like dpx_poopdick_vertical**

→ Simplified version tag stripping logic - removed unnecessary `if '_v' in` check  
→ Regex `^(.+)_v(\d+)$` only matches `_v` followed by digits at END of name  
→ Names like `dpx_poopdick_vertical` now correctly keep full base name  

---

## [1.0.5] - 2025-12-18

**ok it worked for like a few versions now it does not detect the components that are properly prefix'd**

→ Fixed version tag stripping: changed from `split('_v')[0]` to regex `^(.+)_v(\d+)$` to properly handle names like `dpx_valve_v3`  
→ The old split approach would break on names containing `_v` in the middle (e.g., `dpx_valve` → `dpx`)  
→ Added debug output showing each component's name, base name, and prefix match result  
→ Added `component_skipped_count` counter for better diagnostics  
→ Moved `import re` to top of file  

---

## [1.0.4] - 2025-12-13

**ok so this thing isnt actually working on components whats about that**

→ Added explicit root component check using `design.rootComponent` reference before attempting rename  
→ Previously relied on try/except to catch root component error, now proactively skips it  
→ Added separate `component_renamed_count` counter for better feedback  
→ Updated results message to show components and bodies renamed separately  

---

## [1.0.3]

**Failed to execute DPX Versioning: AttributeError: 'Component' object has no attribute 'parentComponent'**

→ Removed faulty `parentComponent` check and added try-except around `comp.name = new_name` to catch root component rename error  

---

## [1.0.2]

**Failed to execute DPX Versioning: RuntimeError: 3 : root component name cannot be changed (still happening)**

→ Changed root component check from `comp != design.rootComponent` to `comp.parentComponent is not None` for more reliable detection  
→ Root component has no parent, so this should properly skip it  

---

## [1.0.1]

**Failed to execute DPX Versioning: RuntimeError: 3 : root component name cannot be changed (again)**

→ Added version constant and startup announcement (v1.0.1) to help identify if changes are loaded  
→ User may need to fully restart Fusion 360 to clear cached add-in code  

---

## [1.0.0]

**Initial release with component support**

**Failed to execute DPX Versioning: RuntimeError: 3 : root component name cannot be changed**

→ Added check to skip renaming the root component (`design.rootComponent`) as it cannot be renamed in Fusion 360  
→ Component renaming now only applies to non-root components that match the prefix  
→ Bodies within the root component can still be renamed if they match  

**ok great next thing we want to do is handle modifying components, as well as bodies. currently the renaming pass does not address component names which it absolutely must to be properly funcitonal. however im unsure if we should be renaming bodies inside the components. lets just keep doing it for now but maybe we put an option in we dont use but its there for later.**

→ Added component renaming alongside body renaming to ensure complete versioning functionality  
→ Introduced `rename_bodies` flag (set to True) for future control over body renaming  
→ Updated descriptions, workflow, examples, and messages to reflect component handling  
→ Restructured the renaming loop to process all components and their bodies  

**hello agent can you please analyze my dpxVersioning.py file and adjust your copilot-instrucitons to write the best possible code for fusion360 plugins? also comment the code accordingly as per the instructions if it is not already**

→ Analyzed dpxVersioning.py code - well-structured Fusion 360 add-in with proper event handling, error management, and UI integration  
→ Updated `.github/copilot-instructions.md` with Fusion 360 specific guidelines for API usage, event handlers, error handling, UI integration, and code patterns  
→ Standardized file header in dpxVersioning.py to match required format with AI rules, project info, and change log  
