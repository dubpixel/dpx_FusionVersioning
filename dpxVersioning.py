# ================================================================================
# PYTHON SCRIPT - FUSION 360 ADD-IN
# ================================================================================
# PROJECT: dpx_FusionVersioning
# ================================================================================
#
# DESCRIPTION:
# This add-in provides automated version tagging for bodies and components in 
# Fusion 360 designs. It identifies bodies and components that match the filename 
# prefix and adds version tags to keep designs organized and synchronized with 
# file versions.
#
# FEATURES:
# - Automatically detects filename prefix (first 3 characters + underscore)
# - Only tags bodies/components that match the file's naming convention
# - Uses file version + 1 to stay synchronized after save
# - Handles both underscore (_) and dash (-) separators
# - Smart version tag replacement (only matches _v followed by digits at end)
# - Auto-saves after renaming to maintain version sync
# - Skips root component (Fusion doesn't allow renaming it)
#
# WORKFLOW:
# 1. User clicks the "DPX Versioning" button in the Modify panel
# 2. Script extracts prefix from filename (e.g., "dpx_widget.f3d" → "dpx_")
# 3. Finds all bodies and components starting with that prefix
# 4. Renames them with next version number (current version + 1)
# 5. Prompts for optional commit message
# 6. Saves the file so versions stay in sync
#
# EXAMPLES:
# - File: "dpx_widget.f3d" (version 3)
# - Components/Bodies: "dpx_lever", "dpx_bracket_v2", "dpx_vertical_mount", "std_screw"
# - Result: "dpx_lever_v4", "dpx_bracket_v4", "dpx_vertical_mount_v4", "std_screw" (unchanged)
# - File saves and becomes version 4
#
# See CHANGELOG.md for version history
# See .github/copilot-instructions.md for development guidelines
#
# ================================================================================

import adsk.core
import adsk.fusion
import traceback
import re
import os

# Add-in version
VERSION = "2.4.3"

# Debug popup behavior for DPX debug info:
# - False: no debug popup during normal operation (recommended)
# - True: always show debug popup
SHOW_DEBUG_POPUP = False

# Sole-untagged-body edge case (see export_bodies): when a tagged component's
# subtree has exactly one body and it's untagged, should that body's actual
# name in the document be updated to match the component (not just the
# exported STL filename)?
# - True: rename the body in the document too
# - False: export under the component's name, leave the document body as-is (default)
RENAME_SOLE_UNTAGGED_BODY = False

# Global list to keep all event handlers in scope.
# This prevents the handlers from being garbage collected.
handlers = []


def matches_prefix(name, file_prefix):
    """
    Check if a name matches the file prefix (supports both _ and - separators).
    
    Args:
        name: The component or body name to check
        file_prefix: The prefix to match (e.g., "dpx_")
    
    Returns:
        bool: True if name matches prefix
    """
    if not name:
        return False
    
    # Strip version tag first to get base name
    match = re.match(r'^(.+)_v(\d+)$', name)
    base_name = match.group(1) if match else name
    base_name_lower = base_name.lower()
    
    prefix_with_dash = file_prefix.replace('_', '-')
    return base_name_lower.startswith(file_prefix) or base_name_lower.startswith(prefix_with_dash)


def update_version_parameter(design, version_number, debug_info=None):
    """
    Create or update a numeric user parameter named 'version' with the current version number.
    
    This provides a workaround for Autodesk breaking the direct parametric text call to versioning.
    Parametric text (sketch text) can now reference the 'version' user parameter instead.
    
    Args:
        design: The active Fusion design
        version_number: The version number to set (integer)
        debug_info: Optional list to append debug messages to
    
    Returns:
        bool: True if parameter was created/updated successfully, False otherwise
    """
    try:
        user_params = design.userParameters
        
        # Check if 'version' parameter already exists
        version_param = user_params.itemByName('version')
        
        if version_param:
            # Parameter exists - update its value
            # User parameters use expressions (strings), not numeric values
            version_param.expression = str(version_number)
            if debug_info is not None:
                debug_info.append(f"[PARAM] Updated 'version' parameter to: {version_number}")
        else:
            # Parameter doesn't exist - create it as an expression
            # Fusion user parameters are created with addByExpression, not addByValue
            # Pass the number as a string expression (e.g., "4")
            user_params.add('version', adsk.core.ValueInput.createByString(str(version_number)), '', 'Version number synchronized with file version')
            if debug_info is not None:
                debug_info.append(f"[PARAM] Created 'version' parameter with value: {version_number}")
        
        return True
    except Exception as e:
        # Log error details for debugging
        error_msg = f"[PARAM] ERROR: Failed to update 'version' parameter: {str(e)}"
        if debug_info is not None:
            debug_info.append(error_msg)
        # Non-fatal error - don't block versioning workflow
        return False


def _collect_export_items(design, file_prefix):
    """
    Scan the design and return tagged export candidates matching file_prefix,
    split into two independent groups.

    Returns:
        dict: {
            'components': [{'type': 'component', 'occurrence': occ, 'name': comp.name}, ...],
            'bodies':     [{'type': 'body', 'body': body, 'name': body.name}, ...],
        }

    Rules:
    - Components: one entry per unique tagged component (first occurrence only,
      de-duplicated). A component placed multiple times would otherwise produce
      N identical STL filenames that silently overwrite each other.
    - Bodies: every tagged body anywhere in the design gets its own entry,
      regardless of whether its parent component is also tagged. The two
      groups are independent selections — checking a component later expands
      to whatever tagged bodies live in its subtree at export time, and a
      body may legitimately appear in both a component's bundle and as its
      own row.
    - Root component itself is never listed as a component (Fusion does not
      allow renaming it, and exporting the entire root is rarely the intent).
      Root-level tagged bodies are still listed under 'bodies'.

    Args:
        design: The active Fusion design
        file_prefix: The prefix to match (e.g., "dpx_")

    Returns:
        dict: {'components': [...], 'bodies': [...]}
    """
    rootComp = design.rootComponent
    components = []
    bodies = []

    # --- Tagged components (de-duplicated to one occurrence each) ---
    # Dedup key must be entityToken, not id(comp) — API proxy objects are
    # transient wrappers whose Python id() can be garbage-collected and
    # recycled for a totally different component mid-loop, which silently
    # drops components from the result (they get marked "already seen").
    seen_comp_tokens = set()
    for comp in design.allComponents:
        if comp == rootComp:
            continue
        if not matches_prefix(comp.name, file_prefix):
            continue
        # Avoid processing the same component definition twice
        if comp.entityToken in seen_comp_tokens:
            continue
        seen_comp_tokens.add(comp.entityToken)
        # Find the FIRST occurrence of this component in the assembly
        for occ in rootComp.allOccurrences:
            if occ.component == comp:
                components.append({
                    'type': 'component',
                    'occurrence': occ,
                    'name': comp.name,
                })
                break  # first occurrence only — prevents duplicate STL filenames

    # --- Tagged bodies, anywhere in the design ---
    # design.allComponents already includes the root component, so root-level
    # bodies are picked up here too without a separate pass.
    for comp in design.allComponents:
        for body in comp.bRepBodies:
            if not body or not matches_prefix(body.name, file_prefix):
                continue
            bodies.append({
                'type': 'body',
                'body': body,
                'name': body.name,
            })

    return {'components': components, 'bodies': bodies}


def _collect_tagged_bodies_recursive(occ, file_prefix):
    """
    Recursively collect tagged bodies (occurrence proxies, so instance
    transforms are correct) from an occurrence's full subtree.

    Walks every child occurrence regardless of whether that nested
    subcomponent is itself tagged — nesting is never a stopping condition.
    Only a body's own name matching file_prefix includes it; untagged
    bodies are never swept in.

    Args:
        occ: The root occurrence to walk (its own bodies are included).
        file_prefix: The prefix to match (e.g., "dpx_")

    Returns:
        list: BRepBody proxies found anywhere in the subtree, tagged only.
    """
    found = []
    for body in occ.bRepBodies:
        if body and body.isValid and matches_prefix(body.name, file_prefix):
            found.append(body)
    for child in occ.childOccurrences:
        found.extend(_collect_tagged_bodies_recursive(child, file_prefix))
    return found


def _walk_occurrence_subtree(occ):
    """Yield occ and every descendant occurrence in its subtree."""
    yield occ
    for child in occ.childOccurrences:
        yield from _walk_occurrence_subtree(child)


def _collect_all_bodies_recursive(occ):
    """
    Recursively collect every body (tagged or not) from an occurrence's
    full subtree. Used only for the sole-untagged-body edge case in
    export_bodies — never to decide what gets exported by default.
    """
    found = []
    for body in occ.bRepBodies:
        if body and body.isValid:
            found.append(body)
    for child in occ.childOccurrences:
        found.extend(_collect_all_bodies_recursive(child))
    return found


def export_bodies(design, file_prefix, ui, items_to_export=None, rename_sole_untagged_body=None):
    """
    Export tagged components/bodies as STL files.

    Export Rules:
    - A tagged component's STL bundle is built from a recursive walk of its
      full occurrence subtree, collecting every tagged body found — nesting
      is never a stopping condition, only a body's own name matters.
    - A component with exactly one tagged body in its subtree exports as
      "{component_name}.stl". A component with multiple tagged bodies
      exports each one individually as "{body_name}.stl" — no merging.
    - A standalone tagged body (its own row, independent of any component
      selection) always exports as "{body_name}.stl".
    - The components list and the bodies list are independent selections:
      a body may legitimately be exported both as part of a component's
      bundle and again as its own standalone row.

    Args:
        design: The active Fusion design.
        file_prefix: The prefix to match (e.g., "dpx_").
        ui: The Fusion UI object for dialogs.
        items_to_export: Optional pre-filtered flat list from the checkbox
            panel (dicts as returned by flattening _collect_export_items'
            'components' + 'bodies' groups). When supplied the scan and
            Yes/No preview dialog are skipped; names are refreshed from live
            Fusion objects so STL filenames reflect any _vN suffix applied
            by the versioning step that just ran.
            When None (default / legacy path), the scan runs here and the
            original Yes/No preview dialog is shown.
        rename_sole_untagged_body: Controls the sole-untagged-body edge case
            (a tagged component whose subtree has exactly one body and it's
            untagged): True renames that body in the document to match the
            component; False exports under the component's name but leaves
            the document body untouched. None (default) falls back to the
            module-level RENAME_SOLE_UNTAGGED_BODY constant.
    """
    try:
        app = adsk.core.Application.get()

        if rename_sole_untagged_body is None:
            rename_sole_untagged_body = RENAME_SOLE_UNTAGGED_BODY

        # ── Determine what to export ─────────────────────────────────────────
        if items_to_export is None:
            # Legacy path: scan + Yes/No preview (used by rename-only button
            # or if the commandCreated scan failed)
            candidates = _collect_export_items(design, file_prefix)
            items_to_export = candidates['components'] + candidates['bodies']

            if len(items_to_export) == 0:
                ui.messageBox(f'No tagged items found to export.\n\nPrefix: {file_prefix}')
                return

            comp_count = len(candidates['components'])
            body_count = len(candidates['bodies'])
            export_list = '\n'.join(f"  • {item['name']}" for item in items_to_export[:10])
            if len(items_to_export) > 10:
                export_list += f"\n  ... and {len(items_to_export) - 10} more"

            result = ui.messageBox(
                f'DPX Export Preview\n\n'
                f'Found {comp_count} components and {body_count} bodies to export:\n'
                f'{export_list}\n\n'
                f'Continue with export?',
                'DPX Version + Export',
                adsk.core.MessageBoxButtonTypes.YesNoButtonType,
            )
            if result != adsk.core.DialogResults.DialogYes:
                return
        else:
            # Interactive path: items already chosen via checkboxes.
            if len(items_to_export) == 0:
                ui.messageBox('No items selected for export.')
                return
            # Refresh names from live Fusion objects so that the _vN suffix
            # applied by the preceding versioning step is reflected in STL
            # filenames. The object references themselves remain valid.
            for item in items_to_export:
                try:
                    if item['type'] == 'component':
                        item['name'] = item['occurrence'].component.name
                    elif item['type'] == 'body':
                        item['name'] = item['body'].name
                except Exception:
                    pass  # keep the pre-versioning name as fallback

        # ── Snapshot original visibility so we can restore later ─────────────
        original_visibility = {}
        for item in items_to_export:
            try:
                if item['type'] == 'component':
                    occ = item['occurrence']
                    original_visibility[occ.entityToken] = occ.isLightBulbOn
                elif item['type'] == 'body':
                    body = item['body']
                    original_visibility[body.entityToken] = body.isLightBulbOn
            except Exception:
                pass

        # Track export results
        exported_count = 0
        failed_items = []
        warnings = []

        # Get the export manager for direct STL export
        exportMgr = design.exportManager

        # Ask user for export directory
        folderDialog = ui.createFolderDialog()
        folderDialog.title = 'Select Export Folder for STL Files'

        dialogResult = folderDialog.showDialog()
        if dialogResult != adsk.core.DialogResults.DialogOK:
            ui.messageBox('Export cancelled.')
            return

        exportPath = folderDialog.folder

        # Export each item one at a time
        for item in items_to_export:
            try:
                if item['type'] == 'component':
                    # Re-fetch the occurrence and component fresh (in case rename invalidated references)
                    occ = item['occurrence']

                    # Verify the occurrence is still valid
                    if not occ or not occ.isValid:
                        failed_items.append(f"{item['name']} (occurrence no longer valid)")
                        continue

                    # Track visibility changes for this export
                    visibility_changes = []

                    # Make every occurrence in the subtree visible — a body is
                    # only actually visible if its full ancestor chain is too.
                    for descendant in _walk_occurrence_subtree(occ):
                        if not descendant.isLightBulbOn:
                            visibility_changes.append(('occ', descendant, False))
                            descendant.isLightBulbOn = True

                    # Walk the full subtree (through nested subcomponents,
                    # tagged or not — nesting is never a stopping condition)
                    # and collect only bodies whose own name is tagged.
                    tagged_bodies = _collect_tagged_bodies_recursive(occ, file_prefix)

                    for body in tagged_bodies:
                        if not body.isLightBulbOn:
                            visibility_changes.append(('body', body, False))
                            body.isLightBulbOn = True

                    if len(tagged_bodies) == 0:
                        # Edge case: nothing tagged in the subtree. If there's
                        # exactly one body total, it's unambiguous which body
                        # was meant — sync its name to the component and
                        # export anyway rather than failing silently.
                        all_bodies = _collect_all_bodies_recursive(occ)
                        if len(all_bodies) == 1:
                            body = all_bodies[0]
                            old_body_name = body.name
                            if not body.isLightBulbOn:
                                visibility_changes.append(('body', body, False))
                                body.isLightBulbOn = True
                            renamed_in_document = False
                            if rename_sole_untagged_body:
                                try:
                                    body.name = item['name']
                                    renamed_in_document = True
                                except Exception:
                                    pass  # export still proceeds under the component's filename
                            try:
                                stlOptions = exportMgr.createSTLExportOptions(body)
                                stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                                stlOptions.filename = os.path.join(exportPath, f"{item['name']}.stl")

                                success = exportMgr.execute(stlOptions)
                                if success:
                                    exported_count += 1
                                    if renamed_in_document:
                                        warnings.append(
                                            f"{item['name']}: sole body '{old_body_name}' was untagged — "
                                            f"renamed to match the component (in document) and exported"
                                        )
                                    else:
                                        warnings.append(
                                            f"{item['name']}: sole body '{old_body_name}' was untagged — "
                                            f"exported under the component's name (document body left unchanged)"
                                        )
                                else:
                                    failed_items.append(f"{item['name']} (Fusion rejected export)")
                            except Exception as export_err:
                                failed_items.append(f"{item['name']} ({str(export_err)})")
                        else:
                            failed_items.append(f"{item['name']} (no tagged bodies found in subtree)")
                    elif len(tagged_bodies) == 1:
                        # Single tagged body — export under the component's own name.
                        body = tagged_bodies[0]
                        try:
                            stlOptions = exportMgr.createSTLExportOptions(body)
                            stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                            stlOptions.filename = os.path.join(exportPath, f"{item['name']}.stl")

                            success = exportMgr.execute(stlOptions)
                            if success:
                                exported_count += 1
                            else:
                                failed_items.append(f"{item['name']} (Fusion rejected export)")
                        except Exception as export_err:
                            failed_items.append(f"{item['name']} ({str(export_err)})")
                    else:
                        # Multiple tagged bodies — export each under its own
                        # already-versioned name, no merging.
                        for body in tagged_bodies:
                            try:
                                stlOptions = exportMgr.createSTLExportOptions(body)
                                stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                                stlOptions.filename = os.path.join(exportPath, f"{body.name}.stl")

                                success = exportMgr.execute(stlOptions)
                                if success:
                                    exported_count += 1
                                else:
                                    failed_items.append(f"{body.name} (Fusion rejected export)")
                            except Exception as export_err:
                                failed_items.append(f"{body.name} ({str(export_err)})")

                    # Restore visibility for this component's subtree
                    for change_type, obj, original_state in visibility_changes:
                        obj.isLightBulbOn = original_state

                elif item['type'] == 'body':
                    # Export body directly
                    body = item['body']
                    original_body_state = body.isLightBulbOn
                    
                    try:
                        # Make the body visible
                        if not body.isLightBulbOn:
                            body.isLightBulbOn = True
                        
                        # Create STL export options for the body
                        stlOptions = exportMgr.createSTLExportOptions(body)
                        stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                        
                        # Set the filename using the item name
                        filename = os.path.join(exportPath, f"{item['name']}.stl")
                        stlOptions.filename = filename
                        
                        # Execute the export
                        success = exportMgr.execute(stlOptions)
                        if success:
                            exported_count += 1
                        else:
                            failed_items.append(f"{item['name']} (Fusion rejected export)")
                    except Exception as export_err:
                        failed_items.append(f"{item['name']} ({str(export_err)})")
                    finally:
                        # Restore body visibility
                        body.isLightBulbOn = original_body_state
                    
            except Exception as e:
                failed_items.append(f"{item['name']} ({str(e)})")
        
        # Restore original occurrence visibility
        for item in items_to_export:
            try:
                if item['type'] == 'component':
                    occ = item['occurrence']
                    token = occ.entityToken
                    if token in original_visibility:
                        occ.isLightBulbOn = original_visibility[token]
            except:
                pass  # Item may have been deleted or modified
        
        # Show summary
        summary = f'DPX Export Complete\n\n'
        summary += f'Exported: {exported_count} STL files to:\n{exportPath}\n'
        if warnings:
            summary += f'\nWarnings ({len(warnings)}):\n'
            summary += '\n'.join([f'  • {w}' for w in warnings[:5]])
            if len(warnings) > 5:
                summary += f'\n  ... and {len(warnings) - 5} more'
        if failed_items:
            summary += f'\nFailed ({len(failed_items)}):\n'
            summary += '\n'.join([f'  • {f}' for f in failed_items[:5]])
            if len(failed_items) > 5:
                summary += f'\n  ... and {len(failed_items) - 5} more'
        
        ui.messageBox(summary)
        
    except:
        ui.messageBox(f'Export failed:\n{traceback.format_exc()}')


def run(context):
    """
    Entry point for the add-in. Called when Fusion 360 loads the add-in.
    Sets up the UI buttons and registers event handlers.
    
    Args:
        context: Fusion 360 context object (not used in this implementation)
    """
    ui = None
    try:
        # Get the Fusion 360 application and UI objects
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get the add-in directory path for resources
        addin_path = os.path.dirname(os.path.realpath(__file__))

        # ==================== BUTTON 1: DPX Versioning ====================
        cmdDef1 = ui.commandDefinitions.itemById('dpxVersioningCmd')
        if not cmdDef1:
            cmdDef1 = ui.commandDefinitions.addButtonDefinition(
                'dpxVersioningCmd',
                'DPX Versioning',
                'Version tag components and bodies matching file prefix',
                os.path.join(addin_path, 'resources')
            )

        onCommandCreated1 = DpxVersioningCommandCreatedHandler(with_export=False)
        cmdDef1.commandCreated.add(onCommandCreated1)
        handlers.append(onCommandCreated1)

        # ==================== BUTTON 2: DPX Version + Export ====================
        cmdDef2 = ui.commandDefinitions.itemById('dpxVersioningExportCmd')
        if not cmdDef2:
            cmdDef2 = ui.commandDefinitions.addButtonDefinition(
                'dpxVersioningExportCmd',
                'DPX Version + Export',
                'Version tag AND export STLs for components/bodies matching file prefix',
                os.path.join(addin_path, 'resources')
            )

        onCommandCreated2 = DpxVersioningCommandCreatedHandler(with_export=True)
        cmdDef2.commandCreated.add(onCommandCreated2)
        handlers.append(onCommandCreated2)

        # ==================== Add buttons to Modify panel ====================
        workspaces = ui.workspaces
        modelingWorkspace = workspaces.itemById('FusionSolidEnvironment')
        
        if modelingWorkspace:
            toolbarPanels = modelingWorkspace.toolbarPanels
            modifyPanel = toolbarPanels.itemById('SolidModifyPanel')
            
            if modifyPanel:
                # Add first button
                buttonControl1 = modifyPanel.controls.itemById('dpxVersioningCmd')
                if not buttonControl1:
                    modifyPanel.controls.addCommand(cmdDef1)
                
                # Add second button
                buttonControl2 = modifyPanel.controls.itemById('dpxVersioningExportCmd')
                if not buttonControl2:
                    modifyPanel.controls.addCommand(cmdDef2)
                    
        ui.messageBox(f'DPX Versioning add-in v{VERSION} loaded!\n\nTwo buttons added to Modify panel:\n• DPX Versioning - tags only\n• DPX Version + Export - tags and exports STLs')

    except:
        if ui:
            ui.messageBox('Failed to initialize DPX Versioning add-in:\n{}'.format(traceback.format_exc()))

def stop(context):
    """
    Called when the add-in is being unloaded. Cleans up UI elements.
    
    Args:
        context: Fusion 360 context object (not used in this implementation)
    """
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Clean up both command definitions
        cmdDef1 = ui.commandDefinitions.itemById('dpxVersioningCmd')
        if cmdDef1:
            cmdDef1.deleteMe()
            
        cmdDef2 = ui.commandDefinitions.itemById('dpxVersioningExportCmd')
        if cmdDef2:
            cmdDef2.deleteMe()

        # Remove both buttons from the Modify panel
        workspaces = ui.workspaces
        modelingWorkspace = workspaces.itemById('FusionSolidEnvironment')
        
        if modelingWorkspace:
            toolbarPanels = modelingWorkspace.toolbarPanels
            modifyPanel = toolbarPanels.itemById('SolidModifyPanel')
            
            if modifyPanel:
                buttonControl1 = modifyPanel.controls.itemById('dpxVersioningCmd')
                if buttonControl1:
                    buttonControl1.deleteMe()
                    
                buttonControl2 = modifyPanel.controls.itemById('dpxVersioningExportCmd')
                if buttonControl2:
                    buttonControl2.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed to clean up DPX Versioning add-in:\n{}'.format(traceback.format_exc()))

class DpxVersioningCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """
    Event handler for when the DPX Versioning command is created.
    Sets up the execute event handler that runs when the button is clicked.
    For the 'Version + Export' button it also populates a native command
    panel with one BoolValueCommandInput checkbox per tagged export candidate.
    """
    def __init__(self, with_export=False):
        super().__init__()
        self.with_export = with_export

    def notify(self, args):
        """
        Called when the command is created. Wires the execute handler and,
        when with_export=True, scans the design and builds the checkbox panel.

        Args:
            args: Command creation event arguments
        """
        try:
            cmd = args.command
            onExecute = DpxVersioningCommandExecuteHandler(with_export=self.with_export)
            cmd.execute.add(onExecute)
            handlers.append(onExecute)  # Keep handler in scope

            # ── Checkbox panel (Version + Export button only) ─────────────────
            if not self.with_export:
                return

            try:
                app = adsk.core.Application.get()
                design = adsk.fusion.Design.cast(app.activeProduct)
                if not design:
                    return
                doc = app.activeDocument
                if not doc or not doc.dataFile:
                    # Unsaved doc — execute will show the proper error; skip panel
                    return

                # Derive prefix the same way execute does
                filename = doc.name
                if '_' in filename:
                    file_prefix = filename.split('_')[0].lower()[:3] + '_'
                else:
                    file_prefix = filename.lower()[:3] + '_'

                candidates = _collect_export_items(design, file_prefix)
                onExecute.export_items = candidates  # pass scan result to execute

                inputs = cmd.commandInputs

                # Show the detected prefix so it's obvious what's being matched
                # before the user scans the lists below.
                inputs.addTextBoxCommandInput(
                    'dpx_detected_prefix',
                    '',
                    f'Detected prefix: "{file_prefix}"',
                    1,
                    True,
                )

                # Top-level setting (not nested in a group) — applies to the
                # sole-untagged-body edge case in a tagged component's subtree.
                inputs.addBoolValueInput(
                    'dpx_rename_sole_untagged',
                    'Rename untagged body',
                    True,   # is a checkbox
                    '',     # no resource icon
                    RENAME_SOLE_UNTAGGED_BODY,  # default: matches the module constant
                )

                comp_candidates = candidates['components']
                body_candidates = candidates['bodies']

                if len(comp_candidates) == 0 and len(body_candidates) == 0:
                    # Still open the panel but tell the user nothing was found
                    inputs.addTextBoxCommandInput(
                        'dpx_no_items',
                        '',
                        f'No tagged items found for prefix  "{file_prefix}".',
                        2,
                        True,
                    )
                    return

                # Two independent groups — check items you want exported as
                # STL. All tagged items get versioned regardless; these
                # checkboxes only control which ones produce an STL file.
                # Checking a component expands to whatever tagged bodies its
                # subtree contains at export time; a body may legitimately
                # also appear checked in its own row. Each group's native
                # collapse/expand doubles as a simple show/hide filter.
                grp_comp = inputs.addGroupCommandInput(
                    'grp_export_components',
                    f'Tagged Components  ({len(comp_candidates)})',
                )
                grp_comp.isExpanded = len(comp_candidates) > 0
                for idx, item in enumerate(comp_candidates):
                    grp_comp.children.addBoolValueInput(
                        f'dpx_export_comp_{idx}',
                        item['name'],
                        True,   # is a checkbox
                        '',     # no resource icon
                        False,  # default: unchecked — bodies are the common case
                    )

                grp_body = inputs.addGroupCommandInput(
                    'grp_export_bodies',
                    f'Tagged Bodies  ({len(body_candidates)})',
                )
                grp_body.isExpanded = len(body_candidates) > 0
                for idx, item in enumerate(body_candidates):
                    grp_body.children.addBoolValueInput(
                        f'dpx_export_body_{idx}',
                        item['name'],
                        True,   # is a checkbox
                        '',     # no resource icon
                        True,   # default: checked
                    )

                # Debug sub-pane — collapsed by default so it stays out of the way.
                grp_debug = inputs.addGroupCommandInput('grp_debug', 'Debug')
                grp_debug.isExpanded = False
                grp_debug.children.addBoolValueInput(
                    'dpx_debug_popup',
                    'Show debug popup',
                    True,   # is a checkbox
                    '',     # no resource icon
                    False,  # default: off  (matches SHOW_DEBUG_POPUP = False)
                )

            except Exception:
                # Panel build failure is non-fatal: execute will fall back to
                # the legacy Yes/No preview path automatically.
                pass

        except Exception:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed to create DPX Versioning command:\n{}'.format(traceback.format_exc()))

class DpxVersioningCommandExecuteHandler(adsk.core.CommandEventHandler):
    """
    Event handler for when the DPX Versioning command is executed.
    Contains the main logic for version tagging bodies.
    """
    def __init__(self, with_export=False):
        super().__init__()
        self.with_export = with_export
        # Populated by DpxVersioningCommandCreatedHandler when the checkbox
        # panel is built successfully. None means fall back to legacy path.
        self.export_items = None

    def notify(self, args):
        """
        Main execution logic. Called when user clicks the DPX Versioning button.
        
        Args:
            args: Command execution event arguments
        """
        ui = None
        try:
            # Get Fusion 360 application and UI
            app = adsk.core.Application.get()
            ui = app.userInterface
            
            # Validate we have an active design
            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                ui.messageBox('No active Fusion design found.')
                return
                
            # Get the current document and its version
            doc = app.activeDocument
            if not doc:
                ui.messageBox('No active document found.')
                return
            
            # Check if document has been saved (unsaved docs have no dataFile)
            if not doc.dataFile:
                ui.messageBox('Please save the document first.\n\nDPX Versioning requires a saved file to determine version numbers.')
                return
                
            # Get current version number from the data file
            verNum = doc.dataFile.versionNumber
            
            # Use version + 1 so that when we save after renaming, the versions match
            # This prevents version drift between file version and body tags
            nextVerNum = verNum + 1
            
            # Initialize debug info collection early so parameter update can log to it
            debug_info = []
            debug_info.append(f"File version (current): v{verNum}")
            debug_info.append(f"Next version (tagging): v{nextVerNum}")
            debug_info.append("")
            
            # Update user parameter 'version' for parametric text references
            # (Autodesk broke direct version access for parametric text)
            param_update_ok = update_version_parameter(design, nextVerNum, debug_info)
            
            # Extract filename prefix for body matching
            # Example: "dpx_widget.f3d" → "dpx_"
            filename = doc.name
            if '_' in filename:
                # Split on underscore and take first part + underscore
                file_prefix = filename.split('_')[0].lower()[:3] + '_'
            else:
                # If no underscore in filename, just use first 3 letters + underscore
                file_prefix = filename.lower()[:3] + '_'
            
            # Option to control body renaming (available for future use)
            rename_bodies = True
            
            # Initialize counters for user feedback
            renamed_count = 0
            skipped_count = 0
            component_renamed_count = 0
            component_skipped_count = 0
            
            # Get reference to root component (cannot be renamed in Fusion 360)
            rootComp = design.rootComponent
            
            # Iterate through all components in the design
            for comp in design.allComponents:
                # Skip the root component - it cannot be renamed in Fusion 360
                if comp == rootComp:
                    debug_info.append(f"[COMP] SKIP ROOT: {comp.name}")
                    continue
                    
                # Rename component if it matches the prefix
                if comp.name:
                    current_name = comp.name
                    
                    # Strip existing version tag (_v followed by digits) to get base name
                    # Only matches _v## at the END of the name, so dpx_vertical stays intact
                    match = re.match(r'^(.+)_v(\d+)$', current_name)
                    baseName = match.group(1) if match else current_name
                        
                    # Check if the BASE name starts with the file prefix
                    # Support both underscore and dash separators
                    base_name_lower = baseName.lower()
                    prefix_with_dash = file_prefix.replace('_', '-')
                    
                    matches = base_name_lower.startswith(file_prefix) or base_name_lower.startswith(prefix_with_dash)
                    
                    debug_info.append(f"[COMP] '{current_name}' → base='{baseName}' lower='{base_name_lower}' prefix='{file_prefix}' match={matches}")
                    
                    if matches:
                        new_name = f"{baseName}_v{nextVerNum}"
                        
                        # ALWAYS set the name - no skip logic
                        # This ensures sync even if it appears to already match
                        try:
                            old_name = comp.name
                            comp.name = new_name
                            component_renamed_count += 1
                            if old_name == new_name:
                                debug_info.append(f"  → SET to '{new_name}' (was already same)")
                            else:
                                debug_info.append(f"  → RENAMED '{old_name}' to '{new_name}'")
                        except RuntimeError as e:
                            debug_info.append(f"  → ERROR: {str(e)}")
                            # Catch any unexpected runtime errors during rename
                            if "root component" in str(e).lower():
                                # Skip root component renaming (backup catch)
                                pass
                            else:
                                raise
                    else:
                        component_skipped_count += 1
                        debug_info.append(f"  → SKIPPED (no prefix match)")
                
                # Rename bodies within the component if enabled
                if rename_bodies:
                    for body in comp.bRepBodies:
                        # Skip invalid bodies
                        if not body or not body.name:
                            debug_info.append(f"  [BODY] SKIP: invalid body")
                            continue
                        
                        # Get the base name by removing any existing version suffix
                        # Only matches _v## at the END of the name, so dpx_vertical stays intact
                        current_name = body.name
                        match = re.match(r'^(.+)_v(\d+)$', current_name)
                        baseName = match.group(1) if match else current_name
                            
                        # Check if the BASE name starts with the file prefix
                        # Support both underscore and dash separators
                        base_name_lower = baseName.lower()
                        prefix_with_dash = file_prefix.replace('_', '-')
                        
                        matches = base_name_lower.startswith(file_prefix) or base_name_lower.startswith(prefix_with_dash)
                        
                        debug_info.append(f"  [BODY] '{current_name}' → base='{baseName}' lower='{base_name_lower}' match={matches}")
                        
                        # Skip bodies that don't match our file prefix
                        if not matches:
                            skipped_count += 1
                            debug_info.append(f"    → SKIPPED (no prefix match)")
                            continue
                        
                        # Create the new name with the next version number
                        new_name = f"{baseName}_v{nextVerNum}"
                        
                        # ALWAYS set the name - no skip logic
                        old_name = body.name
                        body.name = new_name
                        renamed_count += 1
                        if old_name == new_name:
                            debug_info.append(f"    → SET to '{new_name}' (was already same)")
                        else:
                            debug_info.append(f"    → RENAMED '{old_name}' to '{new_name}'")
            
            # Also check root component bodies
            debug_info.append("")
            debug_info.append("[ROOT COMPONENT BODIES]")
            for body in rootComp.bRepBodies:
                if not body or not body.name:
                    continue
                    
                current_name = body.name
                match = re.match(r'^(.+)_v(\d+)$', current_name)
                baseName = match.group(1) if match else current_name
                
                base_name_lower = baseName.lower()
                prefix_with_dash = file_prefix.replace('_', '-')
                
                matches = base_name_lower.startswith(file_prefix) or base_name_lower.startswith(prefix_with_dash)
                
                debug_info.append(f"[BODY] '{current_name}' → base='{baseName}' lower='{base_name_lower}' match={matches}")
                
                if not matches:
                    skipped_count += 1
                    debug_info.append(f"  → SKIPPED (no prefix match)")
                    continue
                
                new_name = f"{baseName}_v{nextVerNum}"
                
                # ALWAYS set the name - no skip logic
                old_name = body.name
                body.name = new_name
                renamed_count += 1
                if old_name == new_name:
                    debug_info.append(f"  → SET to '{new_name}' (was already same)")
                else:
                    debug_info.append(f"  → RENAMED '{old_name}' to '{new_name}'")
            
            # Provide user feedback about what was processed
            total_renamed = renamed_count + component_renamed_count
            
            # Show debug popup only when explicitly enabled, or if parameter sync fails.
            # Prefer the runtime checkbox value (set in the export panel) when available;
            # fall back to the module-level constant for the Version Only path.
            _debug_cb = None
            try:
                _debug_cb = args.command.commandInputs.itemById('dpx_debug_popup')
            except Exception:
                pass
            show_debug = _debug_cb.value if _debug_cb is not None else SHOW_DEBUG_POPUP
            if show_debug or not param_update_ok:
                debug_text = "\n".join(debug_info[:40])  # Limit to 40 lines
                if len(debug_info) > 40:
                    debug_text += f"\n... and {len(debug_info) - 40} more lines"
                title = 'DPX Debug' if show_debug else 'DPX Parameter Sync Warning'
                ui.messageBox(f'DEBUG INFO:\n\n{debug_text}', title)
            
            ui.messageBox(
                f'DPX Versioning v{VERSION}\n\n'
                f'Fusion Filename: {filename}\n'
                f'Version Tag: v{nextVerNum}\n'
                f'Prefix: {file_prefix}\n\n'
                f'Components: {component_renamed_count} Renamed, ({component_skipped_count} Skipped)\n'
                f'Bodies: {renamed_count} Renamed, ({skipped_count} Skipped)'
            )
            
            # Save the document if any bodies/components were renamed
            # This keeps file version in sync with body version tags
            if total_renamed > 0:
                # Default commit message (used as fallback)
                default_commit_message = f"[ v{nextVerNum} ] - |{total_renamed}| {file_prefix} "
                
                # Try to get user comment
                commit_message = default_commit_message
                try:
                    # Prompt user for optional version comment
                    result = ui.inputBox(
                        'Add an optional comment for this version (or leave blank):',
                        'DPX Version Comment',
                        ''
                    )
                    
                    # Fusion 360 API quirk: result[0] = text string, result[1] = boolean BUT INVERTED
                    # result[1] = False means OK clicked, True means Cancel clicked!
                    if not result[1]:  # User clicked OK (result[1] is False)
                        user_comment = result[0].strip() if result[0] else ""
                        
                        if user_comment:
                            # Sanitize comment - remove any problematic characters
                            # Keep only alphanumeric, spaces, basic punctuation
                            sanitized_comment = re.sub(r'[^\w\s\-\.\,\!\?\(\)]', '', user_comment)
                            
                            if sanitized_comment:
                                commit_message = f"[ v{nextVerNum} ] - {sanitized_comment}  - |{total_renamed}| {file_prefix} "
                except Exception as e:
                    # If input dialog fails, just use default message
                    pass
                
                # Save the document with the commit message
                try:
                    doc.save(commit_message)
                    ui.messageBox(f'Document saved! File is now version v{nextVerNum}')
                except:
                    # If save with comment fails, try with default message
                    try:
                        doc.save(default_commit_message)
                        ui.messageBox(f'Document saved! File is now version v{nextVerNum}\n(Note: Custom comment could not be saved)')
                    except:
                        ui.messageBox('Bodies renamed but failed to save document:\n{}'.format(traceback.format_exc()))
            
            # If this is the "Version + Export" button, run export AFTER saving
            # so the file version is correct and all changes are persisted
            if self.with_export:
                if self.export_items is not None:
                    # Interactive path: read checkbox states set by the user
                    # from the two independent groups (components, bodies).
                    inputs = args.command.commandInputs
                    selected = []
                    for idx, item in enumerate(self.export_items.get('components', [])):
                        cb = inputs.itemById(f'dpx_export_comp_{idx}')
                        # If the input is missing (panel build partial failure),
                        # treat it as checked so nothing is silently skipped.
                        if cb is None or cb.value:
                            selected.append(item)
                    for idx, item in enumerate(self.export_items.get('bodies', [])):
                        cb = inputs.itemById(f'dpx_export_body_{idx}')
                        if cb is None or cb.value:
                            selected.append(item)
                    rename_cb = inputs.itemById('dpx_rename_sole_untagged')
                    rename_sole_untagged_body = rename_cb.value if rename_cb is not None else None
                    export_bodies(design, file_prefix, ui, selected, rename_sole_untagged_body)
                else:
                    # Legacy path: scan + Yes/No preview inside export_bodies
                    export_bodies(design, file_prefix, ui)
            
        except:
            if ui:
                ui.messageBox('Failed to execute DPX Versioning:\n{}'.format(traceback.format_exc()))
