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
VERSION = "1.0.9"

# Global list to keep all event handlers in scope.
# This prevents the handlers from being garbage collected.
handlers = []


def export_bodies(design, file_prefix, ui):
    """
    Export bodies matching the prefix to STL files.
    
    Args:
        design: The active Fusion design
        file_prefix: The prefix to match (e.g., "dpx_")
        ui: The Fusion UI object for dialogs
    
    TODO: Implement export logic
    """
    # Placeholder for export functionality
    ui.messageBox(
        f'Export functionality coming soon.\n\n'
        f'Would export all "{file_prefix}" bodies to STL.'
    )
    # TODO: Implement actual export logic here
    # - Get export folder from user
    # - Iterate through bodies matching prefix
    # - Export each as STL


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
            
            # Get reference to root component (cannot be renamed in Fusion 360)
            rootComp = design.rootComponent
            
            # Iterate through all components in the design
            for comp in design.allComponents:
                # Skip the root component - it cannot be renamed in Fusion 360
                if comp == rootComp:
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
                    
                    matches_prefix = base_name_lower.startswith(file_prefix) or base_name_lower.startswith(prefix_with_dash)
                    
                    if matches_prefix:
                        new_name = f"{baseName}_v{nextVerNum}"
                        
                        # Only rename if the name is actually different
                        if comp.name != new_name:
                            try:
                                comp.name = new_name
                                component_renamed_count += 1
                            except RuntimeError as e:
                                # Catch any unexpected runtime errors during rename
                                if "root component" in str(e).lower():
                                    # Skip root component renaming (backup catch)
                                    pass
                                else:
                                    raise
                    else:
                        component_skipped_count += 1
                
                # Rename bodies within the component if enabled
                if rename_bodies:
                    for body in comp.bRepBodies:
                        # Skip invalid bodies
                        if not body or not body.name:
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
                        
                        # Skip bodies that don't match our file prefix
                        if not (base_name_lower.startswith(file_prefix) or base_name_lower.startswith(prefix_with_dash)):
                            skipped_count += 1
                            continue
                        
                        # Create the new name with the next version number
                        new_name = f"{baseName}_v{nextVerNum}"
                        
                        # Only rename if the name is actually different
                        # This avoids unnecessary changes and potential issues
                        if body.name != new_name:
                            body.name = new_name
                            renamed_count += 1
            
            # Provide user feedback about what was processed
            total_renamed = renamed_count + component_renamed_count
            
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
