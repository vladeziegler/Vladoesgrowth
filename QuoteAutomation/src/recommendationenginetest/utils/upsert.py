from pinecone.grpc import PineconeGRPC as Pinecone
import pandas as pd
import time
import uuid
import os
import dotenv

dotenv.load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "clothing-data-2"
CSV_PATH = "/Users/vladimirdeziegler/text_crewai/Vladoesgrowth/QuoteAutomation/sources/ClothingInventory.csv"

def clean_money_value(value):
    """Clean money values by removing commas and converting to float"""
    try:
        if pd.isna(value):
            return 0.0
        return float(str(value).replace(',', ''))
    except (ValueError, TypeError):
        return 0.0

def clean_hours_value(value):
    """Clean hours values by handling NaN and converting to int"""
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (ValueError, TypeError):
        return 0

def prepare_records_from_csv(csv_path, pc):
    """Read CSV and prepare records for Pinecone with proper embeddings,
    tailored for Clothing Inventory records from ClothingInventory.csv."""
    df = pd.read_csv(csv_path)
    print(f"Processing {len(df)} records from CSV...")
    records = []
    
    for idx, row in df.iterrows():
        try:
            # Extract values from CSV row (with basic NaN handling)
            item_code = str(row['item_code']) if not pd.isna(row['item_code']) else ""
            item_description = str(row['item_description']) if not pd.isna(row['item_description']) else ""
            upc_code = str(row['upc_code']) if not pd.isna(row['upc_code']) else ""
            manufacturer_part_number = str(row['manufacturer_part_number']) if not pd.isna(row['manufacturer_part_number']) else ""
            category = str(row['category']) if not pd.isna(row['category']) else ""
            quantity_on_hand = row['quantity_on_hand'] if not pd.isna(row['quantity_on_hand']) else 0
            quantity_allocated = row['quantity_allocated'] if not pd.isna(row['quantity_allocated']) else 0
            quantity_available = row['quantity_available'] if not pd.isna(row['quantity_available']) else 0
            reorder_point = row['reorder_point'] if not pd.isna(row['reorder_point']) else 0
            minimum_stock_level = row['minimum_stock_level'] if not pd.isna(row['minimum_stock_level']) else 0
            maximum_stock_level = row['maximum_stock_level'] if not pd.isna(row['maximum_stock_level']) else 0
            safety_stock = row['safety_stock'] if not pd.isna(row['safety_stock']) else 0
            unit_cost = row['unit_cost'] if not pd.isna(row['unit_cost']) else 0.0
            average_cost = row['average_cost'] if not pd.isna(row['average_cost']) else 0.0
            last_purchase_price = row['last_purchase_price'] if not pd.isna(row['last_purchase_price']) else 0.0
            standard_cost = row['standard_cost'] if not pd.isna(row['standard_cost']) else 0.0
            currency_code = str(row['currency_code']) if not pd.isna(row['currency_code']) else ""
            total_inventory_value = row['total_inventory_value'] if not pd.isna(row['total_inventory_value']) else 0.0
            primary_vendor_id = str(row['primary_vendor_id']) if not pd.isna(row['primary_vendor_id']) else ""
            lead_time_days = row['lead_time_days'] if not pd.isna(row['lead_time_days']) else 0
            last_order_date = str(row['last_order_date']) if not pd.isna(row['last_order_date']) else ""
            last_receipt_date = str(row['last_receipt_date']) if not pd.isna(row['last_receipt_date']) else ""
            preferred_order_quantity = row['preferred_order_quantity'] if not pd.isna(row['preferred_order_quantity']) else 0
            
            # Compose a semantic text description with all the relevant inventory details
            content = (
                f"Inventory Record: Item code '{item_code}' - {item_description}. UPC: {upc_code}. "
                f"Manufacturer Part Number: {manufacturer_part_number}. Category: {category}. "
                f"Stock Details: On hand: {quantity_on_hand}, Allocated: {quantity_allocated}, Available: {quantity_available}. "
                f"Reorder point: {reorder_point}, Minimum stock level: {minimum_stock_level}, Maximum stock level: {maximum_stock_level}, "
                f"Safety stock: {safety_stock}. Pricing Details: Unit cost: {unit_cost} {currency_code}, Average cost: {average_cost}, "
                f"Last purchase price: {last_purchase_price}, Standard cost: {standard_cost}. Total Inventory Value: {total_inventory_value}. "
                f"Vendor: {primary_vendor_id}. Lead Time: {lead_time_days} days. Last Order Date: {last_order_date}, "
                f"Last Receipt Date: {last_receipt_date}. Preferred Order Quantity: {preferred_order_quantity}."
            )
            
            # Generate proper embedding using Pinecone's embedding service
            embedding = pc.inference.embed(
                model="multilingual-e5-large",
                inputs=[content],
                parameters={"input_type": "passage", "truncate": "END"}
            )[0]  # Get the first (and only) embedding result
            
            record = {
                "id": str(uuid.uuid4()),
                "values": embedding.values,  # Embedding vector values
                "metadata": {
                    "content": content,
                    "item_code": item_code,
                    "item_description": item_description,
                    "upc_code": upc_code,
                    "manufacturer_part_number": manufacturer_part_number,
                    "category": category,
                    "quantity_on_hand": quantity_on_hand,
                    "quantity_allocated": quantity_allocated,
                    "quantity_available": quantity_available,
                    "reorder_point": reorder_point,
                    "minimum_stock_level": minimum_stock_level,
                    "maximum_stock_level": maximum_stock_level,
                    "safety_stock": safety_stock,
                    "unit_cost": unit_cost,
                    "average_cost": average_cost,
                    "last_purchase_price": last_purchase_price,
                    "standard_cost": standard_cost,
                    "currency_code": currency_code,
                    "total_inventory_value": total_inventory_value,
                    "primary_vendor_id": primary_vendor_id,
                    "lead_time_days": lead_time_days,
                    "last_order_date": last_order_date,
                    "last_receipt_date": last_receipt_date,
                    "preferred_order_quantity": preferred_order_quantity
                }
            }
            records.append(record)
            
            # Progress reporting every 10 records
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1} records...")
            
            # Small delay to respect rate limits
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error processing record {idx}: {e}")
            continue
    
    return records

def upsert_to_pinecone():
    """Upsert records to Pinecone index"""
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Get the index
    index = pc.Index(name=INDEX_NAME)
    
    # Prepare records with Pinecone client
    records = prepare_records_from_csv(CSV_PATH, pc)
    
    print(f"\nUpserting {len(records)} records to Pinecone...")
    print("\nExample record format:")
    print(records[0])
    
    # Upsert records in batches
    batch_size = 20
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            index.upsert(
                vectors=batch,
                namespace="clothing-data-2"
            )
            print(f"Successfully upserted batch {i//batch_size + 1} of {(len(records) + batch_size - 1)//batch_size}")
            time.sleep(1)  # Rate limiting between batches
            
        except Exception as e:
            print(f"Error upserting batch starting at index {i}: {e}")
            print("First record in failed batch:", batch[0])
            continue
    
    print("\nWaiting for indexing to complete...")
    time.sleep(10)
    
    # Verify the upload
    stats = index.describe_index_stats()
    print("\nIndex Statistics after upload:")
    print(f"Total vectors: {stats.total_vector_count}")
    print(f"Namespaces: {stats.namespaces}")
    
    # Verify a few random records
    print("\nVerifying first few records...")
    for record in records[:3]:
        try:
            result = index.fetch(ids=[record["id"]], namespace="clothing-data-2")
            print(f"Record {record['id']}: {result}")
        except Exception as e:
            print(f"Error fetching record {record['id']}: {e}")

if __name__ == "__main__":
    upsert_to_pinecone()