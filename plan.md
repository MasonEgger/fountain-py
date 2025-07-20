# Minimal Viable Documentation Plan for fountain-py

## Current State Analysis

The fountain-py project has a solid documentation foundation but critical gaps in user-facing content.

**✅ Existing Strengths:**
- Comprehensive Sphinx documentation structure 
- Excellent README.md with clear installation and usage examples
- Well-structured installation guide with platform-specific instructions
- Basic API documentation structure using automodule directives
- Examples directory with working code samples

**❌ Critical Gaps:**
- Most user guide content is placeholder text ("will be completed in Phase X.X")
- quickstart.rst has minimal content - just a basic example
- User guide sections (parsing.rst, elements.rst, rendering.rst) are mostly empty
- No complete end-to-end workflows for common use cases

## Minimal Viable Documentation Strategy

Complete only the **essential user journey** documentation needed for someone to successfully use the library from installation to basic usage.

---

## Implementation Plan: Phase 1 Only (Foundation Content)

### Step 1.1: Complete the Quickstart Tutorial
**Goal:** Replace placeholder quickstart with comprehensive tutorial covering parsing, analysis, and rendering

### Step 1.2: Fill User Guide - Parsing Section  
**Goal:** Complete docs/source/user-guide/parsing.rst with practical parsing examples

### Step 1.3: Fill User Guide - Elements Section
**Goal:** Complete docs/source/user-guide/elements.rst explaining element types and structure

### Step 1.4: Fill User Guide - Rendering Section
**Goal:** Complete docs/source/user-guide/rendering.rst with rendering examples

---

## Implementation Prompts

### Prompt 1: Enhanced Quickstart Tutorial

```text
Complete the quickstart.rst file to provide a comprehensive 10-minute tutorial for fountain-py. The current file has only a basic example. Replace the content with:

1. A practical introduction explaining what users will learn
2. A complete, working example using a realistic Fountain script sample (not just the minimal example currently there)
3. Step-by-step walkthrough showing:
   - How to parse the script and access elements  
   - How to extract characters and analyze the script
   - How to render to HTML and save the output
   - Basic error handling
4. Clear next steps pointing to relevant user guide sections
5. Ensure all code examples are tested and work with the current codebase

The tutorial should be beginner-friendly but practical, giving users confidence they can accomplish real tasks with the library.
```

### Prompt 2: Complete Parsing Documentation

```text
Fill in the user-guide/parsing.rst file which currently has only placeholder content. Create comprehensive documentation for the parsing functionality including:

1. Overview of the FountainParser class and its role
2. Detailed examples showing how to parse Fountain text from strings and files
3. Explanation of the parsing process and what happens under the hood
4. Working with the returned FountainDocument object
5. Understanding different element types in the parsed results
6. Error handling patterns for malformed Fountain text
7. Performance considerations for large scripts
8. Integration with the examples provided in the project

Ensure all code examples are complete, tested, and demonstrate real-world usage patterns.
```

### Prompt 3: Complete Elements Documentation

```text
Fill in the user-guide/elements.rst file to provide comprehensive documentation about Fountain elements. Based on the CLAUDE.md file, there are 14 distinct element types. Create documentation that covers:

1. Overview of the element system and ElementType enum
2. Detailed description of each element type with examples:
   - Scene headers, dialogue, action, transitions
   - Dual dialogue support
   - Character names and parentheticals
   - Notes and boneyard elements
3. Element structure (type, text, formatting, metadata fields)
4. How to access and work with element properties
5. Examples of iterating through and filtering elements
6. Understanding formatting and inline markup
7. Working with element metadata

Include practical examples showing how to extract specific information from scripts using element properties.
```

### Prompt 4: Complete Rendering Documentation

```text
Fill in the user-guide/rendering.rst file to document the rendering system. Currently it's mostly empty. Create comprehensive documentation covering:

1. Overview of the rendering architecture and HTMLRenderer class
2. Basic rendering workflow from FountainDocument to HTML
3. Understanding the default HTML output and CSS classes
4. Customizing HTML output and styling
5. Working with renderer configuration options
6. Saving rendered content to files with proper encoding
7. Understanding the rendering pipeline and how it processes elements
8. Basic overview of creating custom renderers (extensible design mentioned in CLAUDE.md)

Include complete examples showing how to render scripts and customize the output for different use cases.
```

---

## Success Criteria

The minimal viable documentation will be considered complete when:

1. **User Journey is Complete**: A new user can go from installation to productive usage following the documentation
2. **Core Features are Documented**: All major functionality (parsing, elements, rendering) has working examples  
3. **Examples Work**: All code examples in documentation are tested and functional
4. **Placeholder Content is Replaced**: No more "will be completed in Phase X.X" placeholders in user-facing docs