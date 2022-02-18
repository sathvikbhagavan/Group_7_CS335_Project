import pydot

graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")

file1 = open("parser.out", "r")
Lines = file1.readlines()
# Add nodes

for i in range(len(Lines)):
    if Lines[i][0:5] == "state":
        state_number = Lines[i][6:]
        my_node = pydot.Node(state_number)
        graph.add_node(my_node)

# Add edges
for i in range(len(Lines)):
    if Lines[i][0:5] == "state":
        state_number = Lines[i][6:]
        i += 1
        while i < len(Lines) and Lines[i][0:5] != "state":
            if Lines[i].find("shift and go to state") != -1:
                w = Lines[i].split()
                # print(w[0], w[-1])

                if w[0].isupper():
                    graph.add_edge(
                        pydot.Edge(
                            state_number, w[-1], color="black", label=w[0], fontsize=8
                        )
                    )
                else:
                    graph.add_edge(
                        pydot.Edge(
                            state_number, w[-1], color="black", label=w[0], fontsize=10
                        )
                    )
            i += 1
graph.write_raw("graph.dot")
