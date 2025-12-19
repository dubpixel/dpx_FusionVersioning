# Changelog

All notable changes to DPX Fusion Versioning are documented here.

Format: User prompt as single line, followed by itemized solution with → bullet.

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
