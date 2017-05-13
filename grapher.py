import igraph as ig
from pathlib import Path
from random import randint
from math import ceil, sqrt
from PDF import PdfFileWriter, PdfFileReader
import json, sys, getopt, time, os

visual_style = {}
visual_style["bbox"] = [2000, 2000]
visual_style["margin"] = [20, -20] #Not currently in use

#GML naming convention, "GRAPH_NAME.gml"
#Layout naming convention, "GRAPH_NAME.LAYOUT_TYPE.layout"
LAYOUT_TYPES = ["kk", "fr", "lgl", "circle", "drl", "random", "rt", "rt_circular", "sugi", "fr_layer"]
LAYOUT_TYPE_NAMES = {
"kk" : "Kamada Kawai Layout",
"fr" : "Fruchterman Reingold Layout",
"lgl" : "Large Graph Layout",
"circle" : "Circular Layout",
"drl" : "Distributed Recursive Layout",
"random" : "Random Layout",
"rt" : "Reingold-Tilford Tree Layout",
"rt_circular" : "Reingold-Tilford Circular Tree Layout",
"sugi" : "Sugiyama Layout",
"fr_layer" : "Fruchterman Reingold Layered Layout"
}
OUTPUT_TYPES = ["pdf", "svg", "gml", "log"]


def make_Graph_QDIMACS(fname, flatten=True, edge_weight=True, size_range=None, shared_edge_weight=0.1):
    VERTEX_COLORS = ["red", "blue", "green"]
    EDGE_GRADIENT = ["red", "blue"]

    start = time.clock()
    print("Starting to create " + fname + " graph object")

    try:
        file = open(fname + ".qdimacs")
    except:
        print("Failed to open " + fname + ".qdimacs")
        sys.exit()
    header = file.readline()
    while header[0] != "p":
        header = file.readline()
    header = header.split()
    num_vars = int(header[2])
    graph_data = file.read().replace("-", " ").split(" 0\n")	#Removes negations (adds white space to ensure "1-2" -> 1, -2 -> 1, 2) and separates lines
    file.close()

    Graph = ig.Graph()
    Graph["name"] = fname
    Graph.add_vertices(num_vars)

    univ_vars, exis_vars = graph_data[0][1:], graph_data[1][1:]
    if graph_data[0][0] == "e":
        univ_vars, exis_vars = exis_vars, univ_vars
    univ_vars = univ_vars.split()
    exis_vars = exis_vars.split()
    other_vars = [str(i) for i in range(len(univ_vars) + len(exis_vars) + 1, num_vars + 1)]	#This may be a mistake, but reference file mentions one extra variable

    var_type_intermediate = [0] * num_vars
    """
    for i in univ_vars:
        var_type_intermediate[int(i)] = 0
    """
    for i in exis_vars:
        var_type_intermediate[int(i) - 1] = 1
    for i in other_vars:
        var_type_intermediate[int(i) - 1] = 0
    Graph.vs["var_type"] = var_type_intermediate
    
    Graph.vs["color"] = [VERTEX_COLORS[i] for i in Graph.vs["var_type"]]
    Graph.vs["label"] = [str(i + 1) for i in range(num_vars)]
    Graph.vs["label_size"] = [5] * num_vars

    edge_data = [[int(j) - 1 for j in i.split()] for i in graph_data[2:len(graph_data) - 1]]
    for i in edge_data:
        temp_edge_list = []
        for j in i[1:]:
            temp_edge_list.append((i[0], j))
        Graph.add_edges(temp_edge_list)
        
    Graph.es["weight"] = [1] * Graph.ecount()
    Graph.vs["size"] = [8] * num_vars #[float(i) for i in Graph.degree(range(num_vars))]

    if size_range != None: #Expect a tuple, (min, max)
        max_size = max(Graph.vs["size"])
        Graph.vs["size"] = [size_range[0] + (i / max_size * size_range[1]) for i in Graph.vs["size"]]
        for i in Graph.es:
            print(i)
        
    if flatten: #Flatten multigraph, either compute edge weights, or not
        Graph.simplify(combine_edges=(sum if edge_weight else max))
        
    edge_count = Graph.ecount()
    intermediate_weights = Graph.es["weight"]
    palette = ig.GradientPalette(EDGE_GRADIENT[0], EDGE_GRADIENT[1], 3)
    edge_colors = [0] * edge_count
    for i in range(edge_count):
        if Graph.vs["var_type"][Graph.es[i].source] != Graph.vs["var_type"][Graph.es[i].target]:
            intermediate_weights[i] *= shared_edge_weight
            edge_colors[i] = palette.get(1)
        else:
            edge_colors[i] = palette.get(Graph.vs["var_type"][Graph.es[i].source] * 2)
    Graph.es["weight"] = intermediate_weights
    Graph.es["color"] = edge_colors

    
    #This is for coloring edge weights for pdf/svg
    """
    intermediate_weights = abs(intermediate_weights)
    maximal_weight = max(intermediate_weights)
    palette = ig.GradientPalette(EDGE_GRADIENT[0], EDGE_GRADIENT[1], maximal_weight)
    Graph.es["color"] = [palette.get(ceil(i) - 1) for i in Graph.es["weight"]]
    """
    
    print("Graph created in", time.clock() - start, "seconds")
    
    return Graph

def compute_Layout(graph_object, layout_type):
    graph_name = graph_object["name"]
    layout_name = graph_name + ("." if layout_type != "fr" else ".kk.") + layout_type + ".layout"
    layout_file = Path(layout_name)
    if layout_file.is_file():
        layout_file = open(layout_name, 'r')
        layout = ig.Layout(json.load(layout_file), 2)
        layout_file.close()
        return layout
    else:
        start = time.clock()
        print("Starting to compute " + LAYOUT_TYPE_NAMES[layout_type])
        if layout_type == "fr":
            layout = graph_object.layout(layout_type, weights="weight", seed = compute_Layout(graph_object, "kk")) #Takes way more than awhile
            #PROPERLY DONE LIST FOR FR
            #Uses Kamada Kawai for rough initial placement, then sets using Fruchterman Reingold with proper edge weights
        elif layout_type == "sugi":
            layout = graph_object.layout_sugiyama(layers=graph_object.vs["var_type"], weights="weight", hgap = (4 + max(graph_object.vs["size"])) * 2) #Change the hard coding
            visual_style["bbox"][0] *= 4
        elif layout_type == "fr_layer": #Not terribly useful considering the tendency to clump to the dividing line
            var_types = 1 + max(graph_object.vs["var_type"])
            layer_size = visual_style["bbox"][1] / var_types
            minY, maxY = [], []
            for i in range(var_types):
                minY.append(i * layer_size)
                maxY.append((i + 1) * layer_size)
            layout = graph_object.layout_fruchterman_reingold(weights="weight",
            miny=[minY[i] + visual_style["margin"][i % 2] for i in graph_object.vs["var_type"]],
            maxy=[maxY[i] + visual_style["margin"][(i + 1) % 2] for i in graph_object.vs["var_type"]])
        else:
            layout = graph_object.layout(layout_type)	#Takes awhile
        print("Layout computed in", time.clock() - start, "seconds")
        try:
            layout_file = open(layout_name, 'w')
            json.dump(layout.coords, layout_file, separators=(",",":"))
        except:
            print("Error saving " + layout_name)
        return layout

def import_Graph_GML(graph_name):
    graph_file = graph_name + ".gml"
    #Error handling todo
    graph_object = ig.Graph.Read_GML(graph_file)
    graph_object["name"] = graph_name
    return graph_object

def scrub_Vertex_Labels(graph_object):
    graph_object.vs["label"] = ["" for i in graph_object.vs["label"]]
    
def parse_Log(Graph):
    try:
        file = open(Graph["name"] + ".qdimacs.log")
    except:
        print("Failed to open log file")
        sys.exit()
        
    #Make a folder for these, there will be a lot
    os.makedirs("slices_" + Graph["name"], exist_ok=True)
    
    Graph.es["color"] = ["black"] * Graph.ecount()
    
    line = file.readline()  #Skip to the good stuff
    while line[:10] != "Activities":
        line = file.readline()
    
    Dictionary = {}
    num_vars = Graph.vcount()
    
    shapes = ["triangle-down", "circle", "triangle-up"] #Ordering is specific: -1 (False constant), 0 (Non-constant), 1 (True constant)
    
    masterPDF = PdfFileWriter()
    
    count = 1
    while line != "QCNF statistics:\n":
        if line[0] != " ":
            line_list = line[:-1].split(",")
            Dictionary[line_list[0]] = line_list[1:]
        if line[:9] == "Constants":
            #Full dictionary
            #Clean data, dump info
            
            #Activity ~ Size
            Graph.vs["size"] = [10 + 2 * float(i) for i in Dictionary["Activities"]]
            #Decision Level
            decision_level = [int(i) if i != "" else -1 for i in Dictionary["Decision levels"]] #Mark inactive variables, -1
            for i in range(num_vars):
                if Graph.vs["var_type"][i] == 0:
                    decision_level[i] = -2  #Mark universal variables, -2
            palette = ig.GradientPalette("orange", "yellow", max(decision_level) + 1)
            Graph.vs["color"] = [("red" if i == -2 else ("white" if i == -1 else palette.get(i))) for i in decision_level]
            
            #Decision variables
            Graph.vs["frame_color"] = [Graph.vs["color"][i] if Dictionary["Decision variables"][i] == "0" else "green" for i in range(num_vars)]
            #Graph.vs["frame_width"] = [1 if Dictionary["Decision variables"][i] == "0" else 2 for i in range(num_vars)]
            
            #Constants
            Graph.vs["shape"] = [shapes[int(i) + 1] for i in Dictionary["Constants"]]
            
            #Draw
            ig.plot(Graph, "slices_" + Graph["name"] + "\\" + Graph["name"] + "_slice" + str(count) + ".pdf", bbox = visual_style["bbox"])
            masterPDF.addPage(PdfFileReader(open("slices_" + Graph["name"] + "\\" + Graph["name"] + "_slice" + str(count) + ".pdf", "rb")).getPage(0))
            count += 1
            
        line = file.readline()
            
    file.close()
    masterPDF.write(open("slices_" + Graph["name"] + ".pdf","wb"))

def main(argv):
    layout_type = None
    graph_name = ""
    output_type = "pdf"
    import_type = "qdimac"

    try:
        opts, args = getopt.getopt(argv, "hg:l:o:p:q:", ["help", "gml=","layout=", "output=","pickle=","qdimac="])
    except getopt.GetoptError:
        print("Argument Error")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            string = ""
            for i in LAYOUT_TYPE_NAMES:
                string += "\n" + i + "  -  " + LAYOUT_TYPE_NAMES[i]
            print("\n" \
            "-q <qdimac_file_name>\n" \
            "-p <pickle_graph_name>\n" \
            "-g <gml_graph_name>\n" \
            "-l <layout_type>", LAYOUT_TYPES, "\n" \
            "-o <output_type>", OUTPUT_TYPES, "\n\n" \
            "Layout types are as follows:" + string)
                
            sys.exit()
        elif opt in ("-g", "--gml"):
            import_type = "gml"
            graph_name = arg
        elif opt in ("-l", "--layout"):
            if arg in LAYOUT_TYPES:
                layout_type = arg
            else:
                print("Layout Error")
                sys.exit()
        elif opt in ("-o", "--output"):
            if arg in OUTPUT_TYPES:
                output_type = arg
            else:
                print("Output Error")
                sys.exit()
        elif opt in ("-p", "--pickle"):
            import_type = "pickle"
            graph_name = arg
        elif opt in ("-q", "--qdimac"):
            import_type = "qdimac"
            graph_name = arg
            
                
    Graph = None
    if import_type == "qdimac":
        Graph = make_Graph_QDIMACS(graph_name)
    elif import_type == "gml":
        Graph = import_Graph_GML(graph_name)
    elif import_type == "pickle":
        Graph = ig.Graph.Read_Pickle(graph_name + ".pickle")
    else:
        print("Graph import error")
        sys.exit()
        
    if layout_type != None:
        Layout = compute_Layout(Graph, layout_type)
        Graph.vs["x"] = [i[0] for i in Layout.coords]
        Graph.vs["y"] = [i[1] for i in Layout.coords]
        layout_type = "." + layout_type
    else:
        layout_type = ""

    if output_type in ("pdf", "svg"):
        #scrub_Vertex_Labels(Graph)	#Temporary
        ig.plot(Graph, graph_name + layout_type + "." + output_type, bbox = visual_style["bbox"])#, **visual_style)	#Visual style is really handled directly by the graph, saves time recomputing when saved
    elif output_type == "gml":
        Graph.write_gml(graph_name + layout_type + "." + output_type)
    elif output_type == "log":
        parse_Log(Graph)
        
    
	
if __name__ == "__main__":
    main(sys.argv[1:])
	
