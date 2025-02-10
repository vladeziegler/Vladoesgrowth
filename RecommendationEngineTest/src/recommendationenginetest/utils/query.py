from pinecone.grpc import PineconeGRPC as Pinecone
import json

# Configuration
import dotenv
import os
dotenv.load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")

def search_database(query_text, filters=None, top_k=5):
    """
    Search the Pinecone database using gRPC
    Args:
        query_text: The question or search query
        filters: Optional metadata filters
        top_k: Number of results to return
    """
    # Initialize Pinecone with gRPC
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Get the index using host
    index = pc.Index(host=PINECONE_HOST)
    
    try:
        # Convert the query into a vector embedding with input_type parameter
        query_embedding = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[query_text],
            parameters={
                "input_type": "query",
                "truncate": "END"
            }
        )[0]
        
        # Prepare query parameters
        query_params = {
            "namespace": "agents-namespace",
            "vector": query_embedding.values,
            "top_k": top_k,
            "include_metadata": True
        }
        
        # Add filters if provided
        if filters:
            query_params["filter"] = filters
        
        # Perform the search
        results = index.query(**query_params)
        
        # Pretty print the results
        print(f"\nSearch Query: '{query_text}'\n")
        if filters:
            print(f"Filters applied: {filters}\n")
        print("Top Results:")
        
        for idx, match in enumerate(results.matches, 1):
            print(f"\n{idx}. Score: {match.score:.3f}")
            metadata = match.metadata
            print(f"Role: {metadata.get('role', 'N/A')}")
            print(f"Location: {metadata.get('location', 'N/A')}")
            print(f"Company: {metadata.get('company_activity', 'N/A')}")
            print(f"Task: {metadata.get('task', 'N/A')}")
            print(f"Hours Saved: {metadata.get('hours_saved', 'N/A')}")
            print(f"Money Saved: ${float(metadata.get('money_saved', 0)):,.2f}")
            
        return results
        
    except Exception as e:
        print(f"Error during search: {e}")
        print(f"Type of error: {type(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_location_filter(location):
    """Helper function to create location filter"""
    return {"location": {"$eq": location}}

def main():
    # Example queries with optional filters
    example_queries = [
        ("roles where voice agents are most prevalent?", None),
        ("which tasks save the most money?", None),
        ("what are common tasks in marketing?", None),
        ("what tasks are done in New York?", get_location_filter("New York")),
    ]
    
    # Let user choose a query or input their own
    print("Choose a query or type your own:")
    for idx, (query, _) in enumerate(example_queries, 1):
        print(f"{idx}. {query}")
    print("0. Enter your own query")
    
    choice = input("\nEnter your choice (0-4): ")
    
    if choice == "0":
        query_text = input("\nEnter your query: ")
        use_filter = input("Do you want to filter by location? (y/n): ").lower().startswith('y')
        if use_filter:
            location = input("Enter location to filter by: ")
            filters = get_location_filter(location)
        else:
            filters = None
    else:
        try:
            query_text, filters = example_queries[int(choice)-1]
        except (ValueError, IndexError):
            print("Invalid choice. Using default query.")
            query_text, filters = example_queries[0]
    
    # Perform the search with correct argument order
    results = search_database(query_text=query_text, filters=filters)
    
    # Ask if user wants to try another query
    while input("\nWould you like to try another query? (y/n): ").lower().startswith('y'):
        query_text = input("\nEnter your query: ")
        use_filter = input("Do you want to filter by location? (y/n): ").lower().startswith('y')
        if use_filter:
            location = input("Enter location to filter by: ")
            filters = get_location_filter(location)
        else:
            filters = None
        results = search_database(query_text=query_text, filters=filters)

if __name__ == "__main__":
    main()