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
VERSION = "2.1.0"

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


def _collect_export_items(design, file_prefix):
    """
    Scan the design and return a flat list of export candidates matching file_prefix.

    Each entry is a dict:
        {'type': 'component', 'occurrence': occ, 'name': comp.name}
      or
        {'type': 'body', 'body': body, 'name': body.name}

    Rules:
    - Components: one entry per unique component (first occurrence only, de-duplicated).
      A component placed multiple times would otherwise produce N identical STL filenames
      that silently overwrite each other.
    - Bodies: only top-level tagged bodies whose parent component is NOT itself tagged
      (those are exported as part of the parent component's STL).
    - Root component itself is never included (Fusion does not allow renaming it, and
      exporting the entire root is rarely the intent).

    Args:
        design: The active Fusion design
        file_prefix: The prefix to match (e.g., "dpx_")

    Returns:
        list: Ordered list of export-candidate dicts (components first, then bodies).
    """
    rootComp = design.rootComponent
    items = []

    # --- Pass 1: tagged components (de-duplicated to one occurrence each) ---
    seen_comp_ids = set()
    for comp in design.allComponents:
        if comp == rootComp:
            continue
        if not matches_prefix(comp.name, file_prefix):
            continue
        # Avoid processing the same component definition twice
        if id(comp) in seen_comp_ids:
            continue
        seen_comp_ids.add(id(comp))
        # Find the FIRST occurrence of this component in the assembly
        for occ in rootComp.allOccurrences:
            if occ.component == comp:
                items.append({
                    'type': 'component',
                    'occurrence': occ,
                    'name': comp.name,
                })
                break  # first occurrence only — prevents duplicate STL filenames

    # --- Pass 2: tagged bodies NOT inside a tagged component ---
    # Collect tagged component defs for fast membership check
    tagged_comp_set = set()
    for comp in design.allComponents:
        if comp != rootComp and matches_prefix(comp.name, file_prefix):
            tagged_comp_set.add(id(comp))

    # Check all components for tagged bodies.
    # design.allComponents already includes the root component, so we do NOT
    # append rootComp again — that would double-scan root-level bodies.
    for comp in design.allComponents:
        for body in comp.bRepBodies:
            if not body or not matches_prefix(body.name, file_prefix):
                continue
            parent_comp = body.parentComponent
            parent_is_tagged = (parent_comp != rootComp and
                                id(parent_comp) in tagged_comp_set)
            if not parent_is_tagged:
                items.append({
                    'type': 'body',
                    'body': body,
                    'name': body.name,
                })

    # Deduplicate by name: a body and a component may share the same name
    # (e.g. component 'dpx_lever' whose geometry is also a root-level body
    # 'dpx_lever'). The component entry was added first in Pass 1 and wins;
    # the duplicate body entry from Pass 2 is silently dropped.
    seen_names = set()
    unique_items = []
    for item in items:
        if item['name'] not in seen_names:
            seen_names.add(item['name'])
            unique_items.append(item)
    return unique_items


def export_bodies(design, file_prefix, ui, items_to_export=None):
    """
    Export tagged components/bodies as STL files.

    Export Rules:
    - Tagged components/bodies are made visible and exported.
    - A tagged body INSIDE a tagged component is NOT exported separately;
      it is included in the parent component's STL.
    - Untagged sub-components/bodies inside a tagged component are made
      visible so they are captured in the parent STL.
    - Tagged sub-components are hidden during the parent export so they
      get their own separate STL.

    Args:
        design: The active Fusion design.
        file_prefix: The prefix to match (e.g., "dpx_").
        ui: The Fusion UI object for dialogs.
        items_to_export: Optional pre-filtered list from the checkbox panel
            (dicts as returned by _collect_export_items). When supplied the
            scan and Yes/No preview dialog are skipped; names are refreshed
            from live Fusion objects so STL filenames reflect any _vN suffix
            applied by the versioning step that just ran.
            When None (default / legacy path), the scan runs here and the
            original Yes/No preview dialog is shown.
    """
    try:
        app = adsk.core.Application.get()

        # ── Determine what to export ─────────────────────────────────────────
        if items_to_export is None:
            # Legacy path: scan + Yes/No preview (used by rename-only button
            # or if the commandCreated scan failed)
            items_to_export = _collect_export_items(design, file_prefix)

            if len(items_to_export) == 0:
                ui.messageBox(f'No tagged items found to export.\n\nPrefix: {file_prefix}')
                return

            comp_count = sum(1 for x in items_to_export if x['type'] == 'component')
            body_count = sum(1 for x in items_to_export if x['type'] == 'body')
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
                    # Export component via its occurrence
                    occ = item['occurrence']
                    comp = occ.component
                    
                    # Track visibility changes for this export
                    visibility_changes = []
                    
                    # Make the occurrence visible
                    if not occ.isLightBulbOn:
                        visibility_changes.append(('occ', occ, False))
                        occ.isLightBulbOn = True
                    
                    # Collect ALL bodies from this component for export
                    # Tagged bodies inside tagged components were already filtered out 
                    # from getting their own export (lines ~140-147), so they should 
                    # be included in the component export
                    bodies_to_export = []
                    for body in comp.bRepBodies:
                        if body:
                            bodies_to_export.append(body)
                            # Make body visible for export
                            if not body.isLightBulbOn:
                                visibility_changes.append(('body', body, False))
                                body.isLightBulbOn = True
                    
                    # Handle child occurrences (sub-components)
                    # Tagged sub-components get their own export, so hide them
                    for childOcc in occ.childOccurrences:
                        is_tagged = matches_prefix(childOcc.component.name, file_prefix)
                        
                        if is_tagged:
                            # Tagged sub-component - hide it for parent export (gets own export)
                            if childOcc.isLightBulbOn:
                                visibility_changes.append(('childOcc', childOcc, True))
                                childOcc.isLightBulbOn = False
                        else:
                            # Untagged sub-component - make visible for parent export
                            if not childOcc.isLightBulbOn:
                                visibility_changes.append(('childOcc', childOcc, False))
                                childOcc.isLightBulbOn = True
                    
                    if len(bodies_to_export) == 0:
                        failed_items.append(f"{item['name']} (component has no bodies to export)")
                    else:
                        # Create STL export options for the body/bodies
                        if len(bodies_to_export) == 1:
                            exportEntity = bodies_to_export[0]
                        else:
                            # Create a collection for multiple bodies
                            exportEntity = adsk.core.ObjectCollection.create()
                            for body in bodies_to_export:
                                exportEntity.add(body)
                        
                        stlOptions = exportMgr.createSTLExportOptions(exportEntity)
                        stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                        
                        # Set the filename using the item name
                        filename = os.path.join(exportPath, f"{item['name']}.stl")
                        stlOptions.filename = filename
                        
                        # Execute the export — check return value; Fusion returns False on silent failure
                        success = exportMgr.execute(stlOptions)
                        if success:
                            exported_count += 1
                        else:
                            failed_items.append(f"{item['name']} (execute returned False — Fusion rejected the export)")
                    
                    # Restore visibility for this component's children
                    for change_type, obj, original_state in visibility_changes:
                        if change_type == 'occ':
                            obj.isLightBulbOn = original_state
                        elif change_type == 'body':
                            obj.isLightBulbOn = original_state
                        elif change_type == 'childOcc':
                            obj.isLightBulbOn = original_state
                    
                elif item['type'] == 'body':
                    # Export body directly
                    body = item['body']
                    original_body_state = body.isLightBulbOn
                    
                    # Make the body visible
                    if not body.isLightBulbOn:
                        body.isLightBulbOn = True
                    
                    # Create STL export options for the body
                    stlOptions = exportMgr.createSTLExportOptions(body)
                    stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                    
                    # Set the filename using the item name
                    filename = os.path.join(exportPath, f"{item['name']}.stl")
                    stlOptions.filename = filename
                    
                    # Execute the export — check return value; Fusion returns False on silent failure
                    success = exportMgr.execute(stlOptions)
                    if success:
                        exported_count += 1
                    else:
                        failed_items.append(f"{item['name']} (execute returned False — Fusion rejected the export)")
                    
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

                if len(candidates) == 0:
                    # Still open the panel but tell the user nothing was found
                    inputs.addTextBoxCommandInput(
                        'dpx_no_items',
                        '',
                        f'No tagged items found for prefix  "{file_prefix}".',
                        2,
                        True,
                    )
                    return

                # Single flat list — check items you want exported as STL.
                # All tagged items get versioned regardless; these checkboxes
                # only control which ones produce an STL file.
                grp = inputs.addGroupCommandInput(
                    'grp_export',
                    f'Select to export  ({len(candidates)})',
                )
                grp.isExpanded = True
                for idx, item in enumerate(candidates):
                    grp.children.addBoolValueInput(
                        f'dpx_export_{idx}',
                        item['name'],
                        True,   # is a checkbox
                        '',     # no resource icon
                        True,   # default: checked
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
            
            # Debug info collection
            debug_info = []
            debug_info.append(f"File prefix: '{file_prefix}'")
            debug_info.append(f"Next version: v{nextVerNum}")
            debug_info.append("")
            
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
            
            # Debug info is collected but not shown by default
            # Uncomment the lines below to see detailed rename operations:
            # debug_text = "\n".join(debug_info[:40])  # Limit to 40 lines
            # if len(debug_info) > 40:
            #     debug_text += f"\n... and {len(debug_info) - 40} more lines"
            # ui.messageBox(f'DEBUG INFO:\n\n{debug_text}', 'DPX Debug')
            
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
                default_commit_message = f"[▓▓▓ DPX ▓▓▓] Auto-versioned to v{nextVerNum} ({total_renamed} {file_prefix} bodies/components)"
                
                # Try to get user comment
                commit_message = default_commit_message
                try:
                    # Prompt user for optional version comment
                    result = ui.inputBox(
                        'Add an optional comment for this version (or leave blank):',
                        'DPX Version Comment',
                        ''
                    )
                    
                    if result[0]:  # User clicked OK
                        user_comment = result[1].strip() if result[1] else ""
                        if user_comment:
                            # Sanitize comment - remove any problematic characters
                            # Keep only alphanumeric, spaces, basic punctuation
                            sanitized_comment = re.sub(r'[^\w\s\-\.\,\!\?\(\)]', '', user_comment)
                            if sanitized_comment:
                                commit_message = f"{default_commit_message} - {sanitized_comment}"
                except:
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
                    inputs = args.command.commandInputs
                    selected = []
                    for idx, item in enumerate(self.export_items):
                        cb = inputs.itemById(f'dpx_export_{idx}')
                        # If the input is missing (panel build partial failure),
                        # treat it as checked so nothing is silently skipped.
                        if cb is None or cb.value:
                            selected.append(item)
                    export_bodies(design, file_prefix, ui, selected)
                else:
                    # Legacy path: scan + Yes/No preview inside export_bodies
                    export_bodies(design, file_prefix, ui)
            
        except:
            if ui:
                ui.messageBox('Failed to execute DPX Versioning:\n{}'.format(traceback.format_exc()))
