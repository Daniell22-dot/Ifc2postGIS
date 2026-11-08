# ifc2postgis documentation

This folder contains the project documentation.

Start with architecture.md if you want to understand the code.

Start with usage.md if you want to run the converter.

Start with schema.md if you want to query the output database.

## Files

| File            | Purpose                                                    |
|-----------------|------------------------------------------------------------|
| architecture.md | Package layout, data flow, and extension points            |
| schema.md       | Table definitions, relationships, example queries          |
| usage.md        | Installation, command options, and troubleshooting         |

## Contributing

Contributions are welcome. Before opening a pull request, run:

    poetry run black ifc2postgis tests
    poetry run flake8 ifc2postgis tests
    poetry run pytest

The project follows a one-feature-one-commit convention.