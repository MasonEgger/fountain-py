# Examples

This directory contains example scripts demonstrating how to use fountain-py.

## Files

### `convert_macbeth.py`
Converts the Macbeth Fountain script to HTML format, demonstrating basic parsing and HTML rendering.

**Usage:**
```bash
cd examples
python convert_macbeth.py
```

**Output:** Creates `macbeth.html` with the rendered HTML version of the script.

### `test_macbeth_conversion.py`
Test script that validates the Macbeth conversion works correctly.

**Usage:**
```bash
cd examples
python test_macbeth_conversion.py
```

### `macbeth.fountain`
Sample Fountain script containing an excerpt from Shakespeare's Macbeth, adapted to Fountain format.

### `macbeth.md`
Markdown version of the Macbeth script for comparison.

## Running Examples

1. Make sure fountain-py is installed:
   ```bash
   uv sync --dev
   ```

2. Run any example script:
   ```bash
   python examples/convert_macbeth.py
   ```

## Creating Your Own Scripts

You can use these examples as templates for your own Fountain processing scripts. The basic pattern is:

1. Import the parser and renderer
2. Read your Fountain file
3. Parse it with `FountainParser`
4. Render with your chosen renderer
5. Save or display the output

## Additional Examples

For more examples and tutorials, see the [documentation](https://fountain-py.readthedocs.io/en/latest/examples/).