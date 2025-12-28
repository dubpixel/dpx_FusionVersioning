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
VERSION = "1.1.4"

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


def export_bodies(design, file_prefix, ui):
    """
    Export tagged components/bodies via 3D Print command.
    
    Export Rules:
    - Tagged components/bodies are made visible and exported
    - If a tagged item is INSIDE another tagged component and turned off,
      leave it off for the parent export (will get its own sub-export)
    - Untagged bodies inside tagged components should be made visible
    
    Args:
        design: The active Fusion design
        file_prefix: The prefix to match (e.g., "dpx_")
        ui: The Fusion UI object for dialogs
    """
    try:
        app = adsk.core.Application.get()
        
        # Collect all tagged components and bodies
        tagged_components = []
        tagged_bodies = []
        
        rootComp = design.rootComponent
        
        # First pass: identify all tagged items
        for comp in design.allComponents:
            if comp == rootComp:
                continue
            if matches_prefix(comp.name, file_prefix):
                tagged_components.append(comp)
            
            # Check bodies in this component
            for body in comp.bRepBodies:
                if body and matches_prefix(body.name, file_prefix):
                    tagged_bodies.append(body)
        
        # Also check root component bodies
        for body in rootComp.bRepBodies:
            if body and matches_prefix(body.name, file_prefix):
                tagged_bodies.append(body)
        
        # Store original visibility states so we can restore later
        original_visibility = {}
        
        # Track what we'll export
        items_to_export = []
        
        # Process tagged components
        for comp in tagged_components:
            # Find the occurrence(s) of this component
            for occ in rootComp.allOccurrences:
                if occ.component == comp:
                    original_visibility[occ.entityToken] = occ.isLightBulbOn
                    items_to_export.append({
                        'type': 'component',
                        'occurrence': occ,
                        'name': comp.name
                    })
        
        # Process tagged bodies (that aren't inside tagged components)
        for body in tagged_bodies:
            # Check if this body's parent component is tagged
            parent_comp = body.parentComponent
            parent_is_tagged = parent_comp != rootComp and matches_prefix(parent_comp.name, file_prefix)
            
            if not parent_is_tagged:
                original_visibility[body.entityToken] = body.isLightBulbOn
                items_to_export.append({
                    'type': 'body',
                    'body': body,
                    'name': body.name
                })
        
        # Show summary of what will be exported
        comp_count = len([x for x in items_to_export if x['type'] == 'component'])
        body_count = len([x for x in items_to_export if x['type'] == 'body'])
        
        if len(items_to_export) == 0:
            ui.messageBox(f'No tagged items found to export.\n\nPrefix: {file_prefix}')
            return
        
        # List items to export
        export_list = "\n".join([f"  • {item['name']}" for item in items_to_export[:10]])
        if len(items_to_export) > 10:
            export_list += f"\n  ... and {len(items_to_export) - 10} more"
        
        result = ui.messageBox(
            f'DPX Export Preview\n\n'
            f'Found {comp_count} components and {body_count} bodies to export:\n'
            f'{export_list}\n\n'
            f'Continue with export?',
            'DPX Version + Export',
            adsk.core.MessageBoxButtonTypes.YesNoButtonType
        )
        
        if result != adsk.core.DialogResults.DialogYes:
            return
        
        # Track export results
        exported_count = 0
        failed_items = []
        
        # Get the export manager for direct STL export
        exportMgr = design.exportManager
        
        # Get the directory to save exports (same as the Fusion file location)
        # Use the document's dataFile to get the project folder
        doc = app.activeDocument
        
        # Ask user for export directory
        folderDialog = ui.createFolderDialog()
        folderDialog.title = 'Select Export Folder for STL Files'
        
        dialogResult = folderDialog.showDialog()
        if dialogResult != adsk.core.DialogResults.DialogOK:
            ui.messageBox('Export cancelled.')
            return
        
        exportPath = folderDialog.folder
        
        # Build a set of tagged component names for quick lookup
        tagged_comp_names = set(comp.name for comp in tagged_components)
        tagged_body_names = set(body.name for body in tagged_bodies)
        
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
                    
                    # Handle children visibility:
                    # - UNTAGGED bodies/components → make visible (included in parent export)
                    # - TAGGED bodies/components → keep/set hidden (get their own export)
                    
                    # Handle bodies in this component
                    for body in comp.bRepBodies:
                        is_tagged = matches_prefix(body.name, file_prefix)
                        original_state = body.isLightBulbOn
                        
                        if is_tagged:
                            # Tagged body - hide it for parent export (gets own export)
                            if body.isLightBulbOn:
                                visibility_changes.append(('body', body, True))
                                body.isLightBulbOn = False
                        else:
                            # Untagged body - make visible for parent export
                            if not body.isLightBulbOn:
                                visibility_changes.append(('body', body, False))
                                body.isLightBulbOn = True
                    
                    # Handle child occurrences (sub-components)
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
                    
                    # Create STL export options for the component
                    stlOptions = exportMgr.createSTLExportOptions(comp)
                    stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                    
                    # Set the filename using the item name
                    filename = os.path.join(exportPath, f"{item['name']}.stl")
                    stlOptions.filename = filename
                    
                    # Execute the export
                    exportMgr.execute(stlOptions)
                    exported_count += 1
                    
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
                    
                    # Execute the export
                    exportMgr.execute(stlOptions)
                    exported_count += 1
                    
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
    """
    def __init__(self, with_export=False):
        super().__init__()
        self.with_export = with_export

    def notify(self, args):
        """
        Called when the command is created. Sets up the execute handler.
        
        Args:
            args: Command creation event arguments
        """
        try:
            # Connect to the execute event - this runs when user clicks the button
            cmd = args.command
            onExecute = DpxVersioningCommandExecuteHandler(with_export=self.with_export)
            cmd.execute.add(onExecute)
            handlers.append(onExecute)  # Keep handler in scope

        except:
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
            
            # Show debug info first
            debug_text = "\n".join(debug_info[:40])  # Limit to 40 lines
            if len(debug_info) > 40:
                debug_text += f"\n... and {len(debug_info) - 40} more lines"
            ui.messageBox(f'DEBUG INFO:\n\n{debug_text}', 'DPX Debug')
            
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
            
            # If this is the "Version + Export" button, run export after versioning
            if self.with_export:
                export_bodies(design, file_prefix, ui)
            
        except:
            if ui:
                ui.messageBox('Failed to execute DPX Versioning:\n{}'.format(traceback.format_exc()))
