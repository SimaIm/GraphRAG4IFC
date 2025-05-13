import openai
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts.prompt import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
class IFC_QA:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, openai_api_key):
        
        # Initialize Neo4j
        self.graph= Neo4jGraph(neo4j_uri, neo4j_user, neo4j_password)
        
        # Initialize OpenAI
        self.llm = ChatOpenAI(openai_api_key=openai_api_key,temperature=0,model='gpt-4o')

        # Initialize LangChain
        self.cypherChain = None 
        self.template="""
            You are an expert Neo4j Developer translating user questions into Cypher to answer questions about the building information.
            Retrieve relevant building information according to the user question.   
            
            Important Instructions:
            Use only the provided relationship types and properties in the schema.
            Do not use any other relationship types or properties that are not provided in the schema.
            Always refer to the provided Entity-Attribute-Relationship (EAR) Mapping table to ensure that entities, attributes, and relationships are correctly matched.  
            Make sure the query is optimized.
            Do not use any official IFC terms in your answer.

            IFC Instructions:
            -IfcSpace is using for rooms. 
            -Pay attention that roof can be a space (IFcSpace) and the roof (IfcRoof). Differentiate according to user query.
            -Dont use meaningfull variable when writing cypher query, forexample use n1,n2,.. for nodes, and r1,r2,.. for edges.
            -Pay attention to the names as the label and property features follow each other. for exmaple, IfcQuantityLenght has LenghtValue property, or QuantityVolume has VolumeValue property. 
            -If the question is ambiguous, assume the user is asking for the most relevant property in the graph.
            Example: "What is the area?" → Assume both "GrossFloorArea" and "NetFloorArea"
            -Pay attention to make all values integer when using functions like sum().
            -Do not use any official IFC terms in your final answer. Write the inner value as answer, For instance, for IfcLabel('Level: Ground Floor'), write Level: Ground Floor.
            -Do not use UNION in the queries.
            -When writing queries, ensure case-insensitive comparison when matching node properties, relationship properties, or filtering values in a list. Use toLower()

            Example Qusetion and Cypher queries:
            1.
            What materials are used for the walls?:
            MATCH (n1:IfcWall)-[r1:RelatedObjects]-(n2)-[r2:RelatingMaterial]-(n3:IfcMaterialList)-[r3:Materials]-(n4:IfcMaterial) 
            Return Distinct n4.Name
            
            2.
            What is the NetFloorArea of the living room?:
            MATCH (n1:IfcSpace)-[r1:RelatedObjects]-(n2:IfcRelDefinesByProperties)-[r2]-(n3:IfcElementQuantity)-[r3]-(n4:IfcQuantityArea) 
            WHERE toLower(n1.Name) CONTAINS toLower("Living room") AND toLower(n4.Name) CONTAINS toLower("NetFloorArea") Return n4.AreaValue
            
            3.
            What is the height of the Exterior walls in the building?:
            MATCH (n1:IfcWall)-[r1]-(n2:IfcRelDefinesByProperties) -[r2]-(n3:IfcPropertySet)-[r3]-(n4:IfcPropertySingleValue) 
            where toLower(n4.Name) Contains toLower("Height") return n4.NominalValue

            4.
            How many rooms exist in this building?:
            MATCH (n:IfcSpace) RETURN COUNT(n) AS RoomCount

            5. What is the level of the living room?
            MATCH (n1:IfcSpace)-[r1:RelatedObjects]-(n2:IfcRelDefinesByProperties)-[r2]-(n3:IfcPropertySet)-[r3]-(n4:IfcPropertySingleValue) 
            WHERE toLower(n1.Name) CONTAINS toLower("Living room") and toLower(n4.Name) CONTAINS toLower("Level") RETURN n4.NominalValue As Level
            
            Schema : {schema}
            Question : {question}
            """
        
    def initialize_chain(self):
        try:
            schema = self.graph.schema  # Dynamically fetch schema
            cypher_generation_prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=self.template  
        )
            self.cypherChain = GraphCypherQAChain.from_llm(
                        self.llm,
                        graph=self.graph,
                        verbose=True,
                        cypher_prompt=cypher_generation_prompt ,
                        allow_dangerous_requests=True,
                    )   
            print("GraphCypherQAChain initialized successfully!")
        except Exception as e:
             return {"error  initializing chain": str(e)}
        
    def answer(self, question):
        if not self.cypherChain:
            return {"error": "Chain not initialized. Call initialize_chain() first."}

        try:
            input_variables = {"schema": self.graph.schema,"query": question}
            response = self.cypherChain.invoke(input_variables)
            return response

        except Exception as e:
            return {"error": str(e)}
