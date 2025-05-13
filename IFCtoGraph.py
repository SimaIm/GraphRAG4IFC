import ifcopenshell
import networkx as nx
import csv
class IFCtoGraph:
    def __init__(self, ifc_file_path):
        self.ifc_file_path = ifc_file_path
        self.model = None
        self.graph = nx.DiGraph()
        self.header = {}

    def load_ifc(self):
        try:
            self.model = ifcopenshell.open(self.ifc_file_path)
            print("IFC file loaded successfully.")
            self.header = self.model.header  # Store header information
            print(self.header)
        except Exception as e:
            print(f"Failed to load IFC file: {e}")

    def is_ifc_instance_with_id(self,value):
        return isinstance(value, ifcopenshell.entity_instance) and value.id()>0

    def extract_attributes(self, entity):
        attributes = {}
        for attr, value in entity.get_info().items():
            if isinstance(value, ifcopenshell.entity_instance):
                attributes[attr] = {"type": value.is_a(), "id": value.id()}
            elif isinstance(value, (list, tuple)):
                attributes[attr] = [
                    {"type": v.is_a(), "id": v.id()} if isinstance(v, ifcopenshell.entity_instance) else v
                    for v in value
                ]
            else:
                attributes[attr] = value
        return attributes

    def clean_header(self, header):
        try:
            # Safely extract fields from file_name
            file_name = getattr(header, "file_name", None)
            file_name_data = {
                "FileName": getattr(file_name, "name", "Unknown") if hasattr(file_name, "name") else "Unknown",
                "Author": ", ".join(file_name.author) if file_name and hasattr(file_name, "author") and isinstance(file_name.author, (list, tuple)) else "Unknown",
                "Authorization": getattr(file_name, "authorization", "Unknown") if hasattr(file_name, "authorization") else "Unknown",
                "Organization": ", ".join(file_name.organization) if file_name and hasattr(file_name, "organization") and isinstance(file_name.organization, (list, tuple)) else "Unknown",
                "OriginatingSystem": getattr(file_name, "originating_system", "Unknown") if hasattr(file_name, "originating_system") else "Unknown",
                "PreprocessorVersion": getattr(file_name, "preprocessor_version", "Unknown") if hasattr(file_name, "preprocessor_version") else "Unknown",
                "TimeStamp": getattr(file_name, "time_stamp", "Unknown") if hasattr(file_name, "time_stamp") else "Unknown",
            }

            # Safely extract fields from file_description
            file_description = getattr(header, "file_description", None)
            description_data = {
                "Description": ", ".join(file_description.description) if file_description and hasattr(file_description, "description") and isinstance(file_description.description, (list, tuple)) else "Unknown",
                "Thema": getattr(file_description, "thema", "Unknown") if hasattr(file_description, "thema") else "Unknown",
            }

            # Safely extract schema identifiers
            schema = getattr(header, "schema_identifiers", None)
            schema_data = {"Schema": ", ".join(schema) if schema and isinstance(schema, (list, tuple)) else "Unknown"}

            # Combine all fields into one flat dictionary
            header_data = {**file_name_data, **description_data, **schema_data}

            return header_data
        except Exception as e:
            print(f"Failed to clean header: {e}")
            return {"Error": "Header data could not be processed"}


    def build_graph(self):
        if self.model is None:
            print("IFC file not loaded. Call load_ifc() first.")
            return
        print(self.clean_header(self.header))
        self.graph.add_node("000", label="IFC_Header", attributes=self.clean_header(self.header))

        #Get a list of all entity IDs
        entity_ids = sorted([entity.id() for entity in self.model])
        
        # Iterate through all elements in the IFC file
        for id in entity_ids:
            entity=self.model.by_id(id)
            # Filter attributes to only include non-entity_instance and non-empty values
            filtered_attributes = {
            attr: str(value)
            for attr, value in entity.get_info().items()
            if value is not None 
            and not self.is_ifc_instance_with_id(value) # Exclude entity references with IDs
            and not (isinstance(value, (list, tuple)) and all(self.is_ifc_instance_with_id(v) for v in value))  # Exclude lists/tuples of instances with IDs
            and attr not in ["id", "type"]  # Exclude specific keys
            }
            # Add entity to the graph
            self.graph.add_node(entity.id(), label=entity.is_a(), attributes=filtered_attributes)


            # Add relationships
            for attr, value in entity.get_info().items():
                    if self.is_ifc_instance_with_id(value):  # Reference to another IFC entity
                        self.graph.add_edge(entity.id(), value.id(), label=attr)  # Add an edge
                    elif isinstance(value, (list,tuple)):  # List of references
                        for ref in value:
                            if isinstance(ref, ifcopenshell.entity_instance):
                                if self.is_ifc_instance_with_id(ref):
                                    self.graph.add_edge(entity.id(), ref.id(), label=attr)
            
    def save_graph_to_csv(self, node_csv_path, edge_csv_path):
        # Save Nodes
        with open(node_csv_path, mode="w", newline="", encoding="utf-8") as node_file:
            writer = csv.writer(node_file)
            # Write header
            writer.writerow(["id", "label", "attributes"])
            # Write node data
            for node_id, node_data in self.graph.nodes(data=True):
                writer.writerow([
                    node_id,                          # Node ID
                    node_data.get("label", ""),       # Node label (type)
                    str(node_data.get("attributes", ""))  # Attributes as a string
                ])

        # Save Edges
        with open(edge_csv_path, mode="w", newline="", encoding="utf-8") as edge_file:
            writer = csv.writer(edge_file)
            # Write header
            writer.writerow(["start_id", "end_id", "type"])
            # Write edge data
            for source, target, edge_data in self.graph.edges(data=True):
                writer.writerow([
                    source,                           # Start node ID
                    target,                           # End node ID
                    edge_data.get("label", "")        # Edge label (type)
                ])

                
# Example usage:
    # converter = IFCtoGraph(input_file_path)
    # converter.load_ifc()
    # converter.build_graph()
    # converter.save_graph_to_csv(
    #     node_csv_path=node_path,
    #     edge_csv_path=edge_path
    #     )
    # print("Graph exported to CSV format for Neo4j.")

