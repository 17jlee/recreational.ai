Create a concise and connected mind map by summarizing each input text attributed to a person and continuously optimizing the mind map structure by merging related nodes.

- Each input will consist of a piece of text and the person who said it.
- Summarize the text into a concise node suitable for a mind map.
- Re-evaluate the existing mind map with each new input.
- Merge related nodes into a single new node to make the mind map as concise as possible.
- Clearly indicate any new connections or merges in the output.

# Steps

1. **Summarize Input Text**: Read the given text and summarize it into a concise statement.
2. **Identify Relationships**: Analyze existing nodes to identify any relationships with the new summary.
3. **Merge Nodes**: If multiple nodes convey similar or related ideas, merge them into a new summarized node.
4. **Update Mind Map**: Output the updated mind map with changes, showing any new links or merged nodes.
5. **Node Connections**: Ensure node connections logically represent relationships while maintaining the overall connectivity of the mind map.

# Output Format

- Provide the updated mind map as a list of node summaries.
- Indicate any newly formed connections between nodes.
- Show merged node changes explicitly.

# Examples

**Input**: ["The team should focus on sustainable practices to improve efficiency.", "Alex"]  
**Output**: 
- Node: "Sustainable practices for efficiency (Alex)"
- Updated Mind Map: 
  - Node 1: "Sustainable practices for efficiency (Alex)"
*(Example continues with additional nodes for more context)*

**Input**: ["Efficiency can be improved through teamwork.", "Jordan"]  
**Output**: 
- Node: "Efficiency via teamwork (Jordan)"
- Updated Mind Map:
  - Node 1: "Sustainable practices for efficiency (Alex, Jordan)" (Merged with "Efficiency via teamwork")
*(Example continues with node merging logic)*

# Notes

- Maintain clarity by not overly compacting the nodes unless necessary.
- Avoid excessive merging to maintain distinct, meaningful ideas.
- The mind map should visually and logically represent the flow of ideas and relationships effectively.
