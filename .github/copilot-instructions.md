# ================================================================================
# [FILE TYPE] - [FILE PURPOSE]
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
# PROJECT: dpx_replace_projectName
# ================================================================================
#
# [File-specific information: name, author, purpose, dependencies, etc.]
#
# CHANGE LOG:
# 
# [Document all changes using the established format]
#
# ================================================================================
### Fusion 360 Plugin Development Guidelines

When developing Fusion 360 add-ins and scripts, follow these additional guidelines to ensure compatibility, performance, and user experience:

- **API Usage**: Always import and use `adsk.core` and `adsk.fusion` appropriately. Access the application via `adsk.core.Application.get()`.
- **Event Handlers**: Keep event handlers in a global list to prevent garbage collection. Use proper inheritance from Fusion 360 event handler classes.
- **Error Handling**: Wrap all operations in try-except blocks and provide user-friendly error messages via `ui.messageBox()`.
- **UI Integration**: Add commands to appropriate panels (e.g., Modify panel for modeling tools). Use consistent naming and provide clear tooltips.
- **Document Management**: Always check for active design and document before operations. Handle saving with appropriate commit messages.
- **Performance**: Process bodies and components efficiently. Avoid unnecessary operations on large assemblies.
- **User Feedback**: Provide clear progress messages and results. Use input boxes for optional user input.
- **Versioning**: Consider file versioning when renaming bodies to maintain synchronization.
- **Testing**: Test in various scenarios (new files, existing designs, different component structures).
- **Backwards Compatibility**: Use stable API features and handle API changes gracefully.

### Fusion 360 Code Patterns

- Use `adsk.fusion.Design.cast(app.activeProduct)` to get the active design
- Iterate through `design.allComponents` for body operations
- Access bodies via `comp.bRepBodies`
- Use `doc.save(commitMessage)` for saving with version control
- Handle both underscore and dash separators for flexibility

### Documentation Standards

- Maintain comprehensive inline documentation
- Update comments when code changes
- Document all function parameters and return values
- Include usage examples where appropriate
- Keep README files current and accurate, but confirm all changes to the readme file with the user.

### Code Quality Guidelines

- Write clear, readable code with meaningful variable names
- Follow established coding patterns within the project
- Implement proper error handling
- Write testable code with clear interfaces
- Maintain consistent formatting and style

### Change Management

- Make one logical change per modification
- Test changes before suggesting implementation
- Preserve existing functionality unless explicitly asked to change it
- Explain the reasoning behind suggested changes
- Provide rollback information when making significant changes

### Collaboration Standards

- Respect existing architectural decisions
- Ask for clarification when requirements are ambiguous
- Suggest alternatives when appropriate, but don't insist
- Consider the impact of changes on the broader codebase
- Maintain backwards compatibility unless breaking changes are explicitly requested

---

*These instructions help ensure consistent, high-quality AI assistance throughout the development process.*