# Clausal-Graph-Analysis
A tool used to visualize the relationships of variables &amp; clauses in a SAT/2QBF problem; given the proper logging format, it can also step through the solving of the problem in graph form.

## Normal Graphing
This graph will only display relationships between variables and their groupings by type, but will ignore negations.

### Universal Variables:
- Variable Type: 0
- Color: Red
### Existential Variables:
- Variable Type: 1
- Color: Blue
### Other Variables:
###### included for variables that don't fall under the 2QBF format, classified as unviversal variables

### Edges:
- Edges between the same variable type will share an edge of the corresponding color
- Edges between different variable types will share an edge that combines the two colors of the variable nodes
- Contain a weight attribute representing the number of shared clauses between two nodes (a function variable enables by default flattening the multigraph, and another handles the weighting versus simple edges)
- Commented out, but it is possible to color the edges by their weighting

### Layouts:
- Multiple layouts are possible, but force directed graphs have yielded the best outcome (Fruchterman Reingold can take edge weights into account)
- Possible to write new layout types/functions (will be inefficient if written in python)
- Allows for importing and saving of layouts so that their computation only has to be done once

### Logs:
###### Follows a very specific layout for the .qdimacs.log file
File for which the log was processed
SAT Solver and version
Activities, Comma separated activity levels [0.0,float]
Decision levels, Comma separated decision levels [-,0,int]
Decision variables, Comma separated decsions variables [0,1]
Constants, Comma separated constants [-1,0,1]

Then the activities, decisons levels, decision variables, and constants lines are repeated as the solver steps through solving the problem

- Universal variables will be assigned a red color and circle
- Existential variables wll be assigned a color depending on decision level (white is a non-value, and then a gradient from orange to yellow) and shapes will default to a circle, but can be changed
- Constants will overwrite a variable's shape to a triangle, with the point up for True assignments and point down for False
- Activity levels will determine size of the variable drawn
- Decision variables determine where decisions are made during that time slice/step, and will outline the variable in bright green

### Using the program:
The program includes a main directive and funtion so it can be imported for its functions, but usually will be called from the command line. The program includes a help option (-h, --help) which will display available options.
-l, --layout will override the default layout type (will import or compute if not found)
-q, --qdimac tells the program to parse a qdimacs file into a graph
-p, --pickle tells the program to import a python .pickle formatted graph (saves time from parsing and assigning attributes from a .qdimacs file)
-g, --gml similar to the pickle import type, but reads a .gml file (larger than pickle, but usable with other graphing tools)
-o, --output is the output type. This can be a pickle, gml, pdf, svg, or log, important to note is that the log output will create a multipage pdf of the problem being solved (very large file depending on the size of the problem)
