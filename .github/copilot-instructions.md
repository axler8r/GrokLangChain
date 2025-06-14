Use type hints.

Generate pythonic code.

Write docstrings for all functions and classes, following the Google style guide.

Prefer functional code over object-oriented code when appropriate.

Generate code 'top down'.

When instructed to create a new component, only generate enough code to complete
the instruction. Focus only on the current instruction. For example, if I tell
you to create a new component, create as little code as possible to implement
the component. Ask me if it is Okay to continue if you want to generate code
that you were not explicitly instructed to generate. For example, if I tell you
to create class X with certain characteristics, create enough code to implement
the class. If you want to generate generate tests, ask me if it is Okay to
continue.

Use `uv` for package management and virtual environments outside of `Dockerfile`s.

Export dependencies to `requirements.txt` for use inside `Dockerfile`s.
