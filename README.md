
## OBSERVATIONS ABOUT THE USED CFG LIBRARY/TOOL:

In my code, I have mainly used `pycfg.pycfg`: I imported `PyCFG`, `CFGNode`, and `slurp` from this module. `PyCFG` is a class that generates a control flow graph (CFG) from a Python source file. I used `PyCFG` to create the CFG structure, `CFGNode` to represent individual nodes in the graph, and `slurp` to read the source code file.
I have majorly used the ‘pycfg’ library which creates control flow graph and stores information in the nodes of the format: {0: id:0 line[0] parents: [] : start, 1: id:1 line[1] parents: [0] : x = 4, 2: id:2 line[2] parents: [1] : y = 3, 3: id:3 line[3] parents: [2, 5] : _while: (x < 8), 4: id:4 line[4] parents: [3] : z = (x + y), 5: id:5 line[5] parents: [4] : x = (x + 1), 6: id:6 line[6] parents: [3] : print(x, y, z), 7: id:7 line[0] parents: [6] : stop}
This can be neatly represented as nodes such as below:


```
id:1 line[1] parents: [0] : x = 4
Node ID: 1
 Source: x = 4
 Parents: [0]
 Children: [2]
 Calls: []
```

Throughout the code, I have used the logic based on this format and connections between the nodes. Furthermore, the below function tp_graph() helped me visualize by generating a graph and fine tune my logic.

```
g = CFGNode.to_graph(arcs)
g.draw(args.pythonfile + '.png', prog ='dot')
```
Example of a generated control flow graph:
![image](https://github.com/user-attachments/assets/859883d3-0c9d-4e7e-a068-8795765e442a)
## HIGH-LEVEL DESCRIPTION OF IMPLEMENTATION OF THE ANALYSIS: 
### DESCRIPTION OF THE LATTICE:
The lattice used in this analysis defines the parity (even, odd, unknown) of variables and includes four key elements:
BOTTOM: Represents an undefined state for the variable’s parity.
EVEN: Indicates the variable has an even value.
ODD: Indicates the variable has an odd value.
TOP: Represents an unknown or indeterminate state for the variable’s parity, covering cases where the parity cannot be definitively determined.
These are created as global variables which are used in functions for lattice and parity related tasks.
The meet function in the code merges two values within the lattice to determine the least upper bound, using the logic:
```meet(EVEN, EVEN) = EVEN, meet(ODD, ODD) = ODD, meet(TOP, any) = TOP```
When EVEN and ODD are merged, the result is TOP.

### FORWARD AND MAY ANALYSIS:
A Forward Analysis has been conducted: It propagates information from the entry to the exit of each control flow graph (CFG) node, analyzing the program as it moves forward from the start.
This is also a May analysis: The analysis checks for possible states (even, odd, or unknown) that a variable may have at each point, rather than confirming a must state that is guaranteed at every program execution. An example would be when we assess the for or while loop. Some values have the TOP parity as at times they are EVEN and at times ODD.
There are some instances of a Must analysis. For example, when a variable is assigned a literal, such as an integer (e.g., x = 2), the analysis concludes that x must be EVEN. This assignment effectively guarantees the parity in that specific context. This can be seen in all the sample python codes.

### DEFINITIONS FOR THE ABSTRACT OPERATIONS:
meet(a, b): Used to merge two parities. If a and b are the same, it returns that value. If one is BOTTOM, it returns the other. Otherwise, it returns TOP. add_parity(a, b): Defined to handle addition parity based on operand parities:
EVEN + EVEN = EVEN
ODD + ODD = EVEN
EVEN + ODD = ODD
TOP propagates as TOP if either operand is TOP. 
mul_parity(a, b): Handles parity for multiplication:
  If either operand is EVEN, the result is EVEN.
  ODD * ODD = ODD
  
Any operation involving TOP yields TOP. 
def mult_parity_analysis(expr, parity_env, var): Function to perform parity analysis during multiplication def add_parity_analysis(expr, parity_env, var): Function to perform parity analysis during addition def parity_of_literal(value): Function to determine the parity of a literal integer def clean_variable_name(var_name): Function to clean variable names by removing special characters def process_assignment(node, parity_env): Performs functionalities of handling variable and expression parts in a source line of a node when needed in cases of the analyze_parity(). def evaluate_innermost_expr(expr, parity_env): Helps track the innermost parenthesis to perform addition or multiplication operation on and find their respective parity. 
analyze_parity(cfg) : This is one of the most important functions which traverses CFG nodes and merges parity environments for branches (Assignment, Conditions, Control Statements) using meet(a,b).
