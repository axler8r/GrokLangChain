# Overview
You will help me implement a component as part of a **Docker Compose**
application.

Look at the architecture document in `documentation/architecture.md` for an
overview of the project, its components and the expected directory structure.

If you need more information to clarify functionality, requirements or
architecture, ask me questions until you are satisfied that you have enough
information to proceed.

Always ask me one question at a time.

Before you do something, tell me what you are going to do and why you are going
to do it. Then ask me if it is okay to proceed. I will either tell you to
proceed, give you additional instructions or point you in a different
direction.

Complete only one logical step at a time. Ask for my confirmation before
proceeding with the next step. I like to commit small changes often, so try to
keep your changes small and focused. Try to keep code generation and changes
under 150 lines of code at a time.

## Communication Preferences
- Use bullet points for lists of changes or options
- When reporting errors or issues, provide:
  - The specific error message
  - The context where it occurred
  - Suggested fixes with pros/cons
- Format responses with clear sections using markdown headers

## Example workflow
When you implement a new feature together, refactor existing code or fix a bug,
I expect us to work together in the following way:

When you implement a new feature, first create the necessary classes, functions
and types and ask me to review it. Next implement the tests for them. Focus on
unit tests first, we will get to integration tests as a separate activity later.
We will then implement the feature, then write the documentation for it and
update the `Makefile` as it is the driver for all activities. Add logging after
the feature is implemented because logging makes it harder to read the code, so
we will add it last.

If you need to refactor existing code, first write the tests for the code you
are going to refactor, then refactor the code, then run the tests to make sure
everything still works, then write the documentation for the refactored code.

Finally, update the architecture document to reflect the changes you made.

## Testing Guidelines
- Aim for 80% or higher test coverage for new code
- Use pytest as the testing framework
- Name tests using the pattern: `test_<function_name>_<scenario>`
- Include edge cases and error conditions in tests
- Write descriptive test names that explain what is being tested

## Error Handling
- Use specific exception types rather than generic Exception
- Include helpful error messages that guide the user
- Log errors appropriately using the logging module
- Handle errors at the appropriate level (fail fast when appropriate)

## Code Review Checklist
When reviewing code, consider the following in order::
1. **Correctness**: Does the code do what it's supposed to?
1. **Maintainability**: Will this be easy to modify later?
1. **Readability**: Is the code easy to understand?
1. **Security**: Are there any security vulnerabilities?
1. **Style**: Does it follow project conventions?
1. **Performance**: Are there obvious inefficiencies?

## Commit Message Format
Use conventional commits format:
- `feat:` for new features
- `fix:` for bug fixes
- `refactor:` for code refactoring
- `test:` for adding/modifying tests
- `docs:` for documentation changes
- `chore:` for maintenance tasks
- `wip`: work in progress

Example: `feat: add user authentication endpoint`

## Coding Standards
- Follow PEP 8 style guide
- Organize imports alpahbetically:
    - standard library,
    - third-party and,
    - local (separated by blank lines)
- Keep line length under 88 characters
- Use descriptive variable names over comments when possible

## When in Doubt
- Choose readability over cleverness
- Prefer explicit over implicit
- Ask for clarification rather than making assumptions
- Default to more conservative approaches for security-related code
- Follow existing patterns in the codebase

## Guiding principles
- Try your best to keep code changes to less than 150 lines of code.
- Generate code for Python 3.12 and later.
- Use type hints in types, classes, functions and variables.
- Prefer user defined `type`s when it will improve code comprehension and quality.
- Generate docstrings for all public functions and classes, following the
  Google style guide.
- Use `uv` for package management and virtual environments outside of `Dockerfile`s.
- Use `pip` for package management inside `Dockerfile`s.
- Use the `Makefile` as the driver for commands.
- Use long options in `Makefile` target commands.
- Write pythonic code that follows PEP 8 guidelines.

## Documentation Standards
- Document complex algorithms with inline comments
- Include examples in docstrings for public functions
- Keep README files up to date
- Document any non-obvious design decisions
- Use type hints as documentation

## Conclusion
Don't do anything now, I just want you to understand how we will work together.

I will give you further instructions later.

NOW, ASK ME WHAT WE WILL IMPLEMENT TOGETHER.
