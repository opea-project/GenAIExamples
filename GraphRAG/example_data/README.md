# GraphRAG Example Datasets

This directory contains example datasets carefully crafted to demonstrate GraphRAG's capabilities for knowledge graph construction and querying.

## Programming Languages Dataset (`programming_languages.txt`)

A concise dataset that showcases GraphRAG's ability to:

1. **Entity Extraction**

   - People (Guido van Rossum, James Gosling)
   - Organizations (CWI, Sun Microsystems, Google)
   - Programming Languages (Python, Java, ABC, Go)
   - Technologies (REPL, var keyword)

2. **Relationship Types**

   - Creation relationships ("created by")
   - Influence relationships ("influenced by")
   - Employment relationships ("worked at")
   - Usage relationships ("used by")
   - Feature relationships ("borrowed ideas from")

3. **Temporal Information**

   - Creation dates (1991, 1995, 2009)
   - Sequential influences (ABC → Python → Java)

4. **Complex Reasoning Capabilities**
   - Bidirectional influences (Java ↔ Python)
   - Multi-hop relationships (ABC → Python → Java's features)
   - Organizational relationships (Google's use of multiple languages)

### Example Queries

This dataset is ideal for testing queries like:

1. "What are the main themes of the programming dataset?"
2. "What's the relationship between Google and these programming languages?"
3. "How did early teaching languages influence modern programming languages?"
4. "Trace the evolution of programming language features through these languages."
5. "What role did corporate entities play in language development?"

### Community Detection

The dataset is structured to form natural communities around:

- Language Development (Python, ABC, Guido)
- Corporate Influence (Google, Java, Go)
- Language Features (OOP, REPL, var keyword)

This makes it perfect for testing GraphRAG's community detection and summarization capabilities.

### Why Traditional RAG Falls Short

For the example queries above, traditional RAG approaches would struggle in several ways:

1. **Multi-hop Relationships**

   - Traditional RAG: Can only find direct relationships within single documents
   - Example: For "How did ABC influence Java's features?", traditional RAG might miss the connection because it can't trace ABC → Python → Java
   - GraphRAG: Can traverse multiple relationship hops to uncover indirect influences

2. **Community Analysis**

   - Traditional RAG: Limited to keyword matching and proximity-based relationships
   - Example: "What programming language communities formed around Google?" requires understanding organizational and temporal relationships
   - GraphRAG: Can detect and analyze communities through relationship patterns and clustering

3. **Bidirectional Relationships**

   - Traditional RAG: Typically treats relationships as unidirectional text mentions
   - Example: Understanding how Java and Python mutually influenced each other requires tracking bidirectional relationships
   - GraphRAG: Explicitly models bidirectional relationships and their evolution over time

4. **Complex Entity Relationships**

   - Traditional RAG: Struggles to maintain consistency across multiple entity mentions
   - Example: "Trace the evolution of REPL features" requires understanding how the feature moved across languages
   - GraphRAG: Maintains consistent entity relationships across the entire knowledge graph

5. **Temporal Evolution**
   - Traditional RAG: Limited ability to track changes over time
   - Example: Understanding how language features evolved requires tracking temporal relationships
   - GraphRAG: Can model and query temporal relationships between entities

These limitations make traditional RAG less effective for complex queries that require understanding relationships, community structures, and temporal evolution. GraphRAG's knowledge graph approach provides a more complete and accurate representation of these complex relationships.
