from pinecone.grpc import PineconeGRPC as Pinecone
import json

# Configuration
import dotenv
import os
dotenv.load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")

def search_database(query_text, filters=None, top_k=2, namespace="clothing-data-2"):
    """
    Search the Pinecone database using gRPC
    Args:
        query_text: The question or search query
        filters: Optional metadata filters dictionary
        top_k: Number of results to return
        namespace: The namespace to search in
    """
    # Initialize Pinecone with gRPC
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Get the index using host
    index = pc.Index(host=PINECONE_HOST)
    
    try:
        # Convert the query into a vector embedding
        query_embedding = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[query_text],
            parameters={
                "input_type": "query",
                "truncate": "END"
            }
        )[0]
        
        # Example of a range filter for quantity_on_hand between 50 and 150
        quantity_filter = {
            "quantity_on_hand": {
                "$gte": 50,    # Greater than or equal to 50
                "$lte": 150    # Less than or equal to 150
            }
        }
        
        # Prepare query parameters
        query_params = {
            "vector": query_embedding.values,
            "top_k": top_k,
            "include_metadata": True,
            "namespace": namespace,
            "filter": quantity_filter
        }
        
        # Validate and add filters if provided
        if filters and isinstance(filters, dict):
            # Ensure the filter structure is correct
            validated_filter = {}
            for field, conditions in filters.items():
                if isinstance(conditions, dict) and all(op.startswith('$') for op in conditions.keys()):
                    validated_filter[field] = conditions
            
            if validated_filter:
                query_params["filter"] = validated_filter
                
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
            print(f"Item Code: {metadata.get('item_code', 'N/A')}")
            print(f"Description: {metadata.get('item_description', 'N/A')}")
            print(f"UPC Code: {metadata.get('upc_code', 'N/A')}")
            print(f"Manufacturer Part Number: {metadata.get('manufacturer_part_number', 'N/A')}")
            print(f"Category: {metadata.get('category', 'N/A')}")
            print(f"Quantities - On-hand: {metadata.get('quantity_on_hand', 'N/A')}, Allocated: {metadata.get('quantity_allocated', 'N/A')}, Available: {metadata.get('quantity_available', 'N/A')}")
            print(f"Stock Levels - Reorder Point: {metadata.get('reorder_point', 'N/A')}, Min: {metadata.get('minimum_stock_level', 'N/A')}, Max: {metadata.get('maximum_stock_level', 'N/A')}, Safety: {metadata.get('safety_stock', 'N/A')}")
            print(f"Cost Details - Unit Cost: {metadata.get('unit_cost', 'N/A')} {metadata.get('currency_code', '')}, Average Cost: {metadata.get('average_cost', 'N/A')}")
            print(f"Last Purchase Price: {metadata.get('last_purchase_price', 'N/A')}, Standard Cost: {metadata.get('standard_cost', 'N/A')}")
            print(f"Total Inventory Value: {metadata.get('total_inventory_value', 'N/A')}")
            print(f"Vendor: {metadata.get('primary_vendor_id', 'N/A')}")
            print(f"Lead Time (days): {metadata.get('lead_time_days', 'N/A')}")
            print(f"Last Order Date: {metadata.get('last_order_date', 'N/A')}, Last Receipt Date: {metadata.get('last_receipt_date', 'N/A')}")
            print(f"Preferred Order Quantity: {metadata.get('preferred_order_quantity', 'N/A')}")
            
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

def create_filter(**kwargs):
    """
    Helper function to create properly structured filters
    Examples:
        create_filter(
            category=("$eq", "Apparel/T-Shirts"),
            quantity_available=("$lt", 100),
            total_inventory_value=("$gt", 5000)
        )
    """
    filter_dict = {}
    for field, (operator, value) in kwargs.items():
        if operator.startswith('$'):
            filter_dict[field] = {operator: value}
    return filter_dict

def create_range_filter(field, min_value=None, max_value=None):
    """
    Create a range filter for numeric fields
    Args:
        field: The field to filter on
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
    """
    conditions = {}
    if min_value is not None:
        conditions["$gte"] = min_value
    if max_value is not None:
        conditions["$lte"] = max_value
    return {field: conditions}

def main():
    # Example queries relevant to Clothing Inventory
    example_queries = [
        (
            "Show all Apparel/T-Shirts inventory details",
            create_filter(category=("$eq", "Apparel/T-Shirts"))
        ),
        (
            "Which items are low in available stock?",
            create_filter(quantity_available=("$lt", 100))
        ),
        (
            "List items with high inventory value",
            create_filter(total_inventory_value=("$gt", 5000))
        ),
        # Multiple conditions example
        (
            "Low stock T-shirts",
            {
                "category": {"$eq": "Apparel/T-Shirts"},
                "quantity_available": {"$lt": 50}
            }
        )
    ]
    
    # Let user choose a query or input their own
    print("Choose a query or enter your own:")
    for idx, (query, _) in enumerate(example_queries, 1):
        print(f"{idx}. {query}")
    print("0. Enter your own query")
    
    choice = input("\nEnter your choice (0-4): ")
    
    if choice == "0":
        query_text = input("\nEnter your query: ")
        custom_filter = input("Do you want to add a metadata filter? (y/n): ").lower().startswith('y')
        if custom_filter:
            key = input("Enter metadata filter field (e.g., category, primary_vendor_id, total_inventory_value): ")
            op = input("Enter operator (e.g., $eq, $lt, $gt): ")
            value = input("Enter value: ")
            try:
                value = float(value)
            except ValueError:
                pass
            filters = {key: {op: value}}
        else:
            filters = None
    else:
        try:
            query_text, filters = example_queries[int(choice)-1]
        except (ValueError, IndexError):
            print("Invalid choice. Using default query.")
            query_text, filters = example_queries[0]
    
    # Perform the search with the provided query text and metadata filters
    results = search_database(query_text=query_text, filters=filters)
    
    # Ask if user wants to try another query
    while input("\nWould you like to try another query? (y/n): ").lower().startswith('y'):
        query_text = input("\nEnter your query: ")
        custom_filter = input("Do you want to add a metadata filter? (y/n): ").lower().startswith('y')
        if custom_filter:
            key = input("Enter metadata field key (e.g., category, total_inventory_value): ")
            op = input("Enter operator (e.g., $eq, $lt, $gt): ")
            value = input("Enter value: ")
            try:
                value = float(value)
            except ValueError:
                pass
            filters = {key: {op: value}}
        else:
            filters = None
        results = search_database(query_text=query_text, filters=filters)

if __name__ == "__main__":
    main()