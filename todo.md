# Documentation Implementation Todo - Sphinx Edition

## Phase 1: Foundation Migration to Sphinx ⚡

### Step 1.1: Remove MkDocs Dependencies and Add Sphinx ✅
- [x] Enhanced pytest configuration for doctests (--doctest-modules)
- [x] Justfile enhanced with documentation commands (will need updating for Sphinx)
- [x] Basic doctest pytest configuration
- [x] Documentation dependencies framework established (will be migrated to Sphinx)
- [x] Remove MkDocs-specific dependencies from pyproject.toml
- [x] Add comprehensive Sphinx dependencies with theme and extensions
- [x] Remove mkdocs.yml configuration file
- [x] Clean up any MkDocs build artifacts

### Step 1.2: Sphinx Project Initialization 🏗️ ✅
- [x] Initialize Sphinx project in docs/ directory
- [x] Create docs/source/conf.py with professional configuration
- [x] Set up Furo theme with professional styling
- [x] Configure autodoc for automatic API discovery from src/fountain/
- [x] Configure Napoleon for Google-style docstrings
- [x] Create complete directory structure with index.rst files
- [x] Test basic Sphinx build functionality

### Step 1.3: Build System Integration 🔧 ✅
- [x] Update Justfile with Sphinx-specific commands
- [x] Create Makefile in docs/ directory for cross-platform builds (removed for simplicity)
- [x] Configure doctest integration with Sphinx
- [x] Set up development workflow commands
- [x] Test all documentation build commands
- [x] Verify doctest integration works with both pytest and sphinx-build

## Phase 2: API Documentation Enhancement 📚

### Step 2.1: Core Module Docstring Enhancement ✅
- [x] Enhance elements.py with comprehensive Google-style docstrings
  - [x] Document ElementType enum with detailed descriptions and examples
  - [x] Add comprehensive FormatSpan class documentation
  - [x] Document FountainElement class with parameter details
  - [x] Include doctest examples in method docstrings
- [x] Enhance document.py with full documentation
  - [x] Document FountainDocument class thoroughly
  - [x] Add detailed examples to to_dict() and to_json() methods
  - [x] Document analysis methods (get_characters, get_statistics)
  - [x] Include practical usage examples as doctests
- [x] Verify all doctest examples execute correctly with Sphinx
- [x] Update Justfile doctest commands to include pytest doctests

### Step 2.2: Parser Documentation 🔍
- [ ] Document all regex patterns with detailed explanations
  - [ ] SCENE_HEADING_PATTERN and variations
  - [ ] CHARACTER_PATTERN and forced characters
  - [ ] TRANSITION_PATTERN variations
  - [ ] Formatting patterns (bold, italic, underline)
  - [ ] Special element patterns (notes, boneyard, etc.)
- [ ] Add detailed Google-style docstrings to parsing methods
  - [ ] _parse_line method with parsing examples
  - [ ] _parse_title_page with supported field examples
  - [ ] _process_dual_dialogue with complex formatting examples
  - [ ] _extract_formatting with inline formatting examples
- [ ] Document two-pass parsing approach architecture
- [ ] Add doctest examples for complex parsing scenarios

### Step 2.3: Renderer Documentation 🎨
- [ ] Document HTMLRenderer thoroughly
  - [ ] CSS class explanations and styling guide
  - [ ] Theme system documentation and customization options
  - [ ] Output format specification
- [ ] Document FountainRenderer
  - [ ] Round-trip capabilities and limitations
  - [ ] Format preservation guarantees
- [ ] Add custom renderer creation examples
- [ ] Include practical examples of creating custom renderers
- [ ] Add doctest examples for rendering scenarios

## Phase 3: User Documentation 📖

### Step 3.1: Landing Page and Installation 🚀
- [ ] Create compelling docs/source/index.rst
  - [ ] Clear project description and value proposition
  - [ ] Feature highlights with examples
  - [ ] Quick navigation to key sections
  - [ ] Installation teaser with links
- [ ] Write comprehensive docs/source/installation.rst
  - [ ] pip installation instructions
  - [ ] Development installation with uv
  - [ ] Platform-specific notes (Windows, macOS, Linux)
  - [ ] Virtual environment best practices
  - [ ] Installation verification examples
  - [ ] Troubleshooting common issues

### Step 3.2: Quick Start Tutorial ⚡
- [ ] Create step-by-step docs/source/quickstart.rst
  - [ ] Basic parsing example with simple Fountain script
  - [ ] Accessing different element types and properties
  - [ ] Rendering to HTML with styling options
  - [ ] Common use cases (character extraction, scene analysis)
  - [ ] Error handling basics
- [ ] Include practical, runnable examples using existing sample files
- [ ] Add tips and best practices throughout
- [ ] Verify all quickstart examples work

### Step 3.3: Comprehensive User Guide 📖
- [ ] Write docs/source/user-guide/parsing.rst
  - [ ] File parsing vs string parsing
  - [ ] Error handling and validation
  - [ ] Performance considerations and memory usage
  - [ ] Batch processing patterns
- [ ] Create docs/source/user-guide/elements.rst
  - [ ] Detailed explanation of each ElementType
  - [ ] Element relationships and hierarchy
  - [ ] Working with metadata and formatting
  - [ ] Element manipulation and analysis
- [ ] Develop docs/source/user-guide/rendering.rst
  - [ ] HTML rendering options and customization
  - [ ] CSS integration and theming
  - [ ] Fountain format round-trip capabilities
  - [ ] Export options and integration with other tools
- [ ] Add docs/source/user-guide/advanced.rst
  - [ ] Custom parsing workflows
  - [ ] Performance optimization techniques
  - [ ] Integration with other libraries and tools
  - [ ] Advanced batch processing and automation

## Phase 4: Examples and Tutorials 📝

### Step 4.1: Basic Examples
- [ ] Create docs/source/examples/basic-usage.rst
  - [ ] Simple parsing workflow with real scripts
  - [ ] Accessing and working with different element types
  - [ ] Basic statistics and analysis operations
  - [ ] HTML export with custom styling
  - [ ] Common data extraction patterns
- [ ] Add docs/source/examples/script-analysis.rst
  - [ ] Character analysis and dialogue statistics
  - [ ] Scene structure and pacing analysis
  - [ ] Dialogue pattern recognition
  - [ ] Script length and timing calculations
  - [ ] Generating reports and summaries
- [ ] Include complete, runnable examples with explanations
- [ ] Add performance optimization examples

### Step 4.2: Advanced Examples 🚀
- [ ] Create docs/source/examples/custom-renderer.rst
  - [ ] Step-by-step custom renderer implementation
  - [ ] Creating specialized output formats (PDF, JSON, etc.)
  - [ ] Advanced styling and theming techniques
  - [ ] Integration with web frameworks and applications
- [ ] Add docs/source/examples/real-world.rst
  - [ ] Script conversion and migration tools
  - [ ] Automated analysis pipelines
  - [ ] Integration with IDEs and editors
  - [ ] Batch processing workflows for multiple scripts
  - [ ] Performance monitoring and optimization
- [ ] Include complete implementations with explanations
- [ ] Add extensibility guidelines and best practices

## Phase 5: Documentation Infrastructure 🤖

### Step 5.1: Automated API Reference
- [ ] Configure comprehensive Sphinx autodoc for all modules
- [ ] Update docs/source/conf.py for automatic API discovery
- [ ] Create docs/source/api/ structure with index and module pages
- [ ] Set up automatic cross-references between manual and API docs
- [ ] Configure search indexing and optimization
- [ ] Add individual module pages with autodoc directives
- [ ] Ensure seamless integration between manual docs and API docs

### Step 5.2: Documentation Testing and CI 🧪
- [ ] Configure comprehensive Sphinx doctest builder
  - [ ] Run all doctests in documentation and docstrings
  - [ ] Integrate with pytest for unified testing
  - [ ] Add doctest verification to CI pipeline
  - [ ] Handle test isolation and cleanup
- [ ] Add documentation validation
  - [ ] Sphinx build verification (no warnings/errors)
  - [ ] Link checking for external references
  - [ ] Spell checking and grammar validation
  - [ ] Accessibility compliance testing
- [ ] Create CI workflow for documentation
  - [ ] Documentation build testing
  - [ ] Doctest execution and verification
  - [ ] Link validation
  - [ ] Deployment to documentation hosting

## Phase 6: Polish and Deployment 🎯

### Step 6.1: Contributing Documentation 🤝
- [ ] Create docs/source/contributing/development.rst
  - [ ] Development environment setup with uv
  - [ ] Code style guidelines and tooling
  - [ ] Git workflow and branching strategy
  - [ ] Release process and versioning
- [ ] Add docs/source/contributing/testing.rst
  - [ ] Test writing guidelines and patterns
  - [ ] Coverage requirements and reporting
  - [ ] Testing best practices and TDD workflow
  - [ ] CI/CD pipeline explanation
- [ ] Write docs/source/contributing/documentation.rst
  - [ ] Documentation writing guidelines and style
  - [ ] Sphinx and reStructuredText best practices
  - [ ] Review process and approval workflow
  - [ ] Maintenance responsibilities and updates

### Step 6.2: Final Polish and Launch
- [ ] Review all documentation for consistency and accuracy
- [ ] Spell check and grammar review throughout
- [ ] Ensure all code examples work and are up-to-date
- [ ] Verify cross-references and links
- [ ] Configure SEO metadata and descriptions
- [ ] Ensure WCAG 2.1 AA accessibility compliance
- [ ] Set up analytics and user feedback systems
- [ ] Deploy to Read the Docs or GitHub Pages
- [ ] Create documentation maintenance and update plan

## Current Status: Phase 1 Complete - Ready for Phase 2

**Next Action**: Begin Phase 2.1 - Core Module Docstring Enhancement

**Phase 1 Completed**: ✅ Sphinx foundation migration complete with professional documentation structure

## Migration Notes
- **Completed Foundation Work**: Pytest doctest configuration and basic Justfile commands are ready to be adapted for Sphinx
- **Key Migration**: Replace MkDocs toolchain with professional Sphinx documentation system
- **Benefit**: Sphinx provides superior autodoc capabilities and professional documentation standards
- **Timeline**: Foundation migration should complete quickly, then proceed with enhanced API documentation

## Success Criteria for Sphinx Migration
- **Professional Appearance**: Clean, modern Furo theme
- **Automated API Docs**: Complete autodoc integration with Google-style docstrings
- **Testing Integration**: Comprehensive doctest integration with both pytest and Sphinx
- **Developer Experience**: Intuitive commands and workflow for documentation development
- **Production Ready**: Deployment to professional documentation hosting