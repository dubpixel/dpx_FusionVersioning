# ================================================================================
# PYTHON SCRIPT - FUSION 360 ADD-IN
# ================================================================================
#
# This project includes AI-generated code assistance provided by GitHub Copilot.
# 
# GitHub Copilot is an AI programming assistant that helps developers write code
# more efficiently by providing suggestions and completing code patterns.
#
# Ground Rules for AI Assistance:
# - No modifications to working code without explicit request
# - Comprehensive commenting of all code and preservation of existing comments
#   (remove comments that become false/obsolete)
# - Small, incremental changes to maintain code stability
# - Verification before implementation of any suggestions
# - Stay focused on the current task - do not jump ahead or suggest next steps
# - Answer only what is asked - do not anticipate or propose additional work
# - ALL user prompts and AI solutions must be documented in the change log comments
#   - Format: User prompt as single line, followed by itemized solution with → bullet
#
# The AI assistant will follow these directives to ensure code quality,
# maintainability, and collaborative development practices.
#
# ================================================================================
# PROJECT: dpx_FusionVersioning
# ================================================================================
#
# File-specific information: dpxVersioning.py, author: DPX Team, purpose: Automated version tagging for bodies in Fusion 360 designs, dependencies: adsk.core, adsk.fusion
#
# DESCRIPTION:
# This add-in provides automated version tagging for bodies in Fusion 360 designs.
# It identifies bodies that match the filename prefix and adds version tags to keep
# designs organized and synchronized with file versions.
#
# FEATURES:
# - Automatically detects filename prefix (first 3 characters + underscore)
# - Only tags bodies that match the file's naming convention
# - Uses file version + 1 to stay synchronized after save
# - Handles both underscore (_) and dash (-) separators
# - Removes existing version tags before applying new ones
# - Auto-saves after renaming to maintain version sync
#
# WORKFLOW:
# 1. User clicks the "DPX Versioning" button in the Modify panel
# 2. Script extracts prefix from filename (e.g., "dpx_widget.f3d" → "dpx_")
# 3. Finds all bodies starting with that prefix
# 4. Renames them with next version number (current version + 1)
# 5. Saves the file so versions stay in sync
#
# EXAMPLES:
# - File: "dpx_widget.f3d" (version 3)
# - Bodies: "dpx_lever", "dpx_bracket_v2", "std_screw"
# - Result: "dpx_lever_v4", "dpx_bracket_v4", "std_screw" (unchanged)
# - File saves and becomes version 4
#
# Created by: DPX Team
# Version: 1.0
# Based on: versionTagBodies
#
# CHANGE LOG:
#
# hello agent can you please analyze my dpxVersioning.py file and adjust your copilot-instrucitons to write the best possible code for fusion360 plugins? also comment the code accordingly as per the instructions if it is not already
# → Analyzed dpxVersioning.py code - well-structured Fusion 360 add-in with proper event handling, error management, and UI integration
# → Updated .github/copilot-instructions.md with Fusion 360 specific guidelines for API usage, event handlers, error handling, UI integration, and code patterns
# → Standardized file header in dpxVersioning.py to match required format with AI rules, project info, and change log
#
# ================================================================================

import adsk.core
import adsk.fusion
import traceback

# Global list to keep all event handlers in scope.
# This prevents the handlers from being garbage collected.
handlers = []

def run(context):
    """
    Entry point for the add-in. Called when Fusion 360 loads the add-in.
    Sets up the UI button and registers event handlers.
    
    Args:
        context: Fusion 360 context object (not used in this implementation)
    """
    ui = None
    try:
        # Get the Fusion 360 application and UI objects
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Create a command definition for our DPX versioning tool
        # Check if the command already exists to avoid duplicates
        cmdDef = ui.commandDefinitions.itemById('dpxVersioningCmd')
        if not cmdDef:
            # Get the add-in directory path for resources
            import os
            addin_path = os.path.dirname(os.path.realpath(__file__))
            
            # Create the button definition with proper icon paths
            cmdDef = ui.commandDefinitions.addButtonDefinition(
                'dpxVersioningCmd',                                    # Command ID
                'DPX Versioning',                                      # Button text
                'DPX company versioning tool - tags bodies by prefix', # Tooltip
                os.path.join(addin_path, 'resources')                 # Icon directory
            )

        # Connect to the command created event
        # This sets up what happens when the user clicks our button
        onCommandCreated = DpxVersioningCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)  # Keep handler in scope

        # Get the MODIFY panel in the MODEL workspace to add our button
        workspaces = ui.workspaces
        modelingWorkspace = workspaces.itemById('FusionSolidEnvironment')
        
        if modelingWorkspace:
            toolbarPanels = modelingWorkspace.toolbarPanels
            modifyPanel = toolbarPanels.itemById('SolidModifyPanel')
            
            if modifyPanel:
                # Add the command button to the Modify panel
                buttonControl = modifyPanel.controls.itemById('dpxVersioningCmd')
                if not buttonControl:
                    buttonControl = modifyPanel.controls.addCommand(cmdDef, 'SolidModifyPanel')
                    
        ui.messageBox('DPX Versioning add-in loaded!\nLook for the "DPX Versioning" button in the Modify panel.')

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

        # Clean up the command definition
        cmdDef = ui.commandDefinitions.itemById('dpxVersioningCmd')
        if cmdDef:
            cmdDef.deleteMe()

        # Remove the button from the Modify panel
        workspaces = ui.workspaces
        modelingWorkspace = workspaces.itemById('FusionSolidEnvironment')
        
        if modelingWorkspace:
            toolbarPanels = modelingWorkspace.toolbarPanels
            modifyPanel = toolbarPanels.itemById('SolidModifyPanel')
            
            if modifyPanel:
                buttonControl = modifyPanel.controls.itemById('dpxVersioningCmd')
                if buttonControl:
                    buttonControl.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed to clean up DPX Versioning add-in:\n{}'.format(traceback.format_exc()))

class DpxVersioningCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """
    Event handler for when the DPX Versioning command is created.
    Sets up the execute event handler that runs when the button is clicked.
    """
    def __init__(self):
        super().__init__()

    def notify(self, args):
        """
        Called when the command is created. Sets up the execute handler.
        
        Args:
            args: Command creation event arguments
        """
        try:
            # Connect to the execute event - this runs when user clicks the button
            cmd = args.command
            onExecute = DpxVersioningCommandExecuteHandler()
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
    def __init__(self):
        super().__init__()

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
            
            # Initialize counters for user feedback
            renamed_count = 0
            skipped_count = 0
            
            # Iterate through all components and their bodies in the design
            for comp in design.allComponents:
                # Skip components with no bodies
                if not comp.bRepBodies:
                    continue
                    
                # Process each body in the component
                for body in comp.bRepBodies:
                    # Skip invalid bodies
                    if not body or not body.name:
                        continue
                    
                    # Get the base name by removing any existing version suffix
                    # Example: "dpx_lever_v3" → "dpx_lever"
                    current_name = body.name
                    if '_v' in current_name:
                        baseName = current_name.split('_v')[0]
                    else:
                        baseName = current_name
                        
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
            ui.messageBox(
                f'DPX Versioning Results:\n'
                f'File prefix: {file_prefix}\n'
                f'Renamed {renamed_count} bodies with version tag v{nextVerNum} (current v{verNum} + 1)\n'
                f'Skipped {skipped_count} bodies (prefix mismatch)'
            )
            
            # Save the document if any bodies were renamed
            # This keeps file version in sync with body version tags
            if renamed_count > 0:
                # Default commit message (used as fallback)
                default_commit_message = f"[▓▓▓ DPX ▓▓▓] Auto-versioned to v{nextVerNum} ({renamed_count} {file_prefix} bodies)"
                
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
                            import re
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
            
        except:
            if ui:
                ui.messageBox('Failed to execute DPX Versioning:\n{}'.format(traceback.format_exc()))
