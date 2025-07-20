Quick Start
===========

This tutorial will guide you through using fountain-py to parse, analyze, and render Fountain screenplay files in just 10 minutes. By the end, you'll be able to work with professional screenplay formats programmatically.

What You'll Learn
-----------------

- How to parse Fountain scripts from text and files
- How to analyze scripts to extract characters, scenes, and statistics
- How to render scripts to properly formatted HTML
- How to handle common errors and edge cases

Installation
------------

First, ensure fountain-py is installed:

.. code-block:: bash

   pip install fountain-py

Working with a Complete Script
------------------------------

Let's work with a realistic screenplay excerpt that demonstrates various Fountain elements:

.. code-block:: python

   from fountain import FountainParser
   
   # A sample screenplay excerpt with various elements
   screenplay_text = """
   Title: The Coffee Shop Connection
   Author: Jane Doe
   Draft date: 2024-01-15
   
   FADE IN:
   
   INT. COFFEE SHOP - DAY
   
   A bustling neighborhood COFFEE SHOP. The afternoon sun streams through 
   large windows. Business people and students hunker over laptops.
   
   ALICE (28), creative but frazzled, sits at a corner table, staring at 
   her laptop screen. She sighs and rubs her temples.
   
   ALICE
   (muttering to herself)
   Come on, inspiration... where are you?
   
   The door chimes. BOB (30s), confident but approachable, enters and 
   scans the crowded shop. The only empty seat is across from Alice.
   
   BOB
   Excuse me, is this seat taken?
   
   ALICE
   (barely looking up)
   No, go ahead.
   
   Bob sits. They work in silence. Then:
   
   BOB
   Writer's block?
   
   ALICE
   (surprised)
   How did you--?
   
   BOB
   The temple rubbing. Dead giveaway.
   (extends hand)
   Bob. Fellow sufferer.
   
   ALICE
   (smiling despite herself)
   Alice. What's your poison? Novel? 
   Screenplay?
   
   BOB
   Startup pitch deck.
   
   ALICE
   (laughing)
   That's even worse!
   
   CUT TO:
   
   INT. COFFEE SHOP - LATER
   
   Alice and Bob's laptops are pushed aside. Coffee cups multiply.
   They're deep in animated conversation.
   
   ALICE
   So your app matches writers with 
   coffee shops based on their 
   creative energy?
   
   BOB
   Exactly! And the algorithm considers 
   noise levels, wifi speed, coffee 
   quality...
   
   ALICE
   (excited)
   You could add a "writer's block 
   breaker" feature!
   
   [[Note: This is where their collaboration begins]]
   
   FADE OUT.
   """
   
   # Parse the screenplay
   parser = FountainParser()
   document = parser.parse(screenplay_text)
   
   print(f"Successfully parsed screenplay with {len(document.elements)} elements")

Analyzing Script Elements
-------------------------

Once parsed, you can explore the document structure and extract useful information:

.. code-block:: python

   # Access title page metadata
   print("\n=== SCRIPT METADATA ===")
   for key, value in document.metadata.items():
       print(f"{key}: {value}")
   
   # Extract and display all characters
   print("\n=== CHARACTERS ===")
   characters = document.get_characters()
   for character in sorted(characters):
       print(f"- {character}")
   
   # Get all scene headings
   print("\n=== SCENES ===")
   scenes = document.get_scenes()
   for i, scene in enumerate(scenes, 1):
       print(f"{i}. {scene}")
   
   # Get comprehensive statistics
   print("\n=== SCRIPT STATISTICS ===")
   stats = document.get_statistics()
   for stat_name, count in stats.items():
       if count > 0:  # Only show non-zero stats
           # Convert stat names to readable format
           readable_name = stat_name.replace('_', ' ').title()
           print(f"{readable_name}: {count}")

Working with Individual Elements
--------------------------------

You can iterate through elements and access their properties:

.. code-block:: python

   from fountain import ElementType
   
   # Find all dialogue from a specific character
   print("\n=== ALICE'S DIALOGUE ===")
   alice_speaking = False
   for element in document.elements:
       if element.type == ElementType.CHARACTER and "ALICE" in element.text:
           alice_speaking = True
       elif element.type == ElementType.DIALOGUE and alice_speaking:
           print(f"- {element.text}")
       elif element.type not in [ElementType.DIALOGUE, ElementType.PARENTHETICAL]:
           alice_speaking = False
   
   # Find all action lines that introduce characters
   print("\n=== CHARACTER INTRODUCTIONS ===")
   for element in document.elements:
       if element.type == ElementType.ACTION:
           # Look for character introductions (typically with age in parentheses)
           if "(" in element.text and any(char in element.text for char in characters):
               print(f"- {element.text[:60]}...")
   
   # Extract all parentheticals (stage directions)
   print("\n=== STAGE DIRECTIONS ===")
   for element in document.elements:
       if element.type == ElementType.PARENTHETICAL:
           print(f"- {element.text}")

Rendering to HTML
-----------------

Convert your parsed screenplay to properly formatted HTML:

.. code-block:: python

   # Generate HTML with screenplay formatting
   html_output = document.to_html()
   
   # Save to file with proper encoding
   output_file = "screenplay.html"
   with open(output_file, 'w', encoding='utf-8') as f:
       f.write(html_output)
   
   print(f"\nScreenplay rendered to {output_file}")
   
   # The HTML includes embedded CSS for proper screenplay formatting
   # Preview what the HTML contains
   print("\nHTML Preview (first 500 chars):")
   print(html_output[:500] + "...")

Parsing from Files
------------------

In practice, you'll often work with .fountain files:

.. code-block:: python

   # Parse directly from a file
   parser = FountainParser()
   
   # Using a file path
   document = parser.parse_file("my_screenplay.fountain")
   
   # Or read and parse manually for more control
   with open("my_screenplay.fountain", 'r', encoding='utf-8') as f:
       fountain_text = f.read()
   document = parser.parse(fountain_text)

Error Handling
--------------

Handle common issues gracefully:

.. code-block:: python

   from fountain import FountainParser
   import os
   
   def safe_parse_file(filepath):
       """Safely parse a Fountain file with error handling."""
       parser = FountainParser()
       
       # Check if file exists
       if not os.path.exists(filepath):
           print(f"Error: File '{filepath}' not found")
           return None
       
       try:
           # Attempt to parse the file
           document = parser.parse_file(filepath)
           print(f"Successfully parsed: {filepath}")
           
           # Verify we got elements
           if not document.elements:
               print("Warning: Document appears to be empty")
           
           return document
           
       except UnicodeDecodeError:
           print(f"Error: File encoding issue. Ensure '{filepath}' is UTF-8 encoded")
           return None
       except Exception as e:
           print(f"Error parsing file: {e}")
           return None
   
   # Use the safe parser
   doc = safe_parse_file("screenplay.fountain")
   if doc:
       print(f"Parsed {len(doc.elements)} elements")

Working with Different Output Formats
-------------------------------------

Fountain-py supports multiple output formats:

.. code-block:: python

   # Convert to different formats
   document = parser.parse(screenplay_text)
   
   # HTML for web display
   html = document.to_html()
   
   # JSON for data interchange
   json_data = document.to_json()
   print("\nJSON output (first 200 chars):")
   print(json_data[:200] + "...")
   
   # Python dictionary for further processing
   dict_data = document.to_dict()
   print(f"\nDictionary has keys: {list(dict_data.keys())}")
   print(f"Number of elements: {len(dict_data['elements'])}")

Complete Example: Script Analysis Tool
--------------------------------------

Here's a complete example that ties everything together:

.. code-block:: python

   from fountain import FountainParser
   import json
   
   def analyze_screenplay(filepath):
       """Analyze a screenplay and generate a report."""
       parser = FountainParser()
       
       try:
           # Parse the screenplay
           document = parser.parse_file(filepath)
           
           # Create analysis report
           report = {
               'title': document.metadata.get('title', 'Untitled'),
               'author': document.metadata.get('author', 'Unknown'),
               'statistics': document.get_statistics(),
               'characters': sorted(document.get_characters()),
               'scenes': document.get_scenes(),
               'scene_count': len(document.get_scenes()),
               'page_estimate': document.get_statistics().get('dialogue', 0) // 20  # Rough estimate
           }
           
           # Generate HTML version
           html_path = filepath.replace('.fountain', '.html')
           with open(html_path, 'w', encoding='utf-8') as f:
               f.write(document.to_html())
           
           # Save analysis report
           report_path = filepath.replace('.fountain', '_analysis.json')
           with open(report_path, 'w', encoding='utf-8') as f:
               json.dump(report, f, indent=2)
           
           print(f"Analysis complete!")
           print(f"- HTML output: {html_path}")
           print(f"- Analysis report: {report_path}")
           
           return report
           
       except Exception as e:
           print(f"Error analyzing screenplay: {e}")
           return None
   
   # Use the analyzer
   if __name__ == "__main__":
       report = analyze_screenplay("my_screenplay.fountain")
       if report:
           print(f"\nScript: {report['title']} by {report['author']}")
           print(f"Scenes: {report['scene_count']}")
           print(f"Characters: {', '.join(report['characters'])}")

Next Steps
----------

Now that you understand the basics, explore these areas:

- **Parsing Deep Dive**: Learn about parsing options and advanced patterns in :doc:`user-guide/parsing`
- **Element Types**: Understand all 15 Fountain elements in detail in :doc:`user-guide/elements`  
- **Custom Rendering**: Create custom output formats in :doc:`user-guide/rendering`
- **API Reference**: Explore the complete API in :doc:`api/index`

You're now ready to work with professional screenplays programmatically using fountain-py!