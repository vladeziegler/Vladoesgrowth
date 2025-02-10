from pinecone.grpc import PineconeGRPC as Pinecone
import pandas as pd
import time
import uuid
import os
import dotenv

dotenv.load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "agents-data-3"
CSV_PATH = "/Users/vladimirdeziegler/text_crewai/Vladoesgrowth/RecommendationEngineTest/sources/agents_data.csv"

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
    """Read CSV and prepare records for Pinecone with proper embeddings"""
    df = pd.read_csv(csv_path)
    print(f"Processing {len(df)} records from CSV...")
    records = []
    
    for idx, row in df.iterrows():
        try:
            # Clean values
            money_saved = clean_money_value(row['moneySaved'])
            hours_saved = clean_hours_value(row['hoursSaved'])
            
            # Create semantic text for embedding - improved format
            content = f"A {row['Role']} working in {row['Location']} at a {row['companyActivity']} company performs the task: {row['Task']}. This task takes {hours_saved} hours and costs ${money_saved}."
            
            # Generate proper embedding using Pinecone's embedding service
            embedding = pc.inference.embed(
                model="multilingual-e5-large",
                inputs=[content],
                parameters={"input_type": "passage", "truncate": "END"}
            )[0]  # Get first element of the response
            
            record = {
                "id": str(uuid.uuid4()),
                "values": embedding.values,  # Access the values from the embedding
                "metadata": {
                    "content": content,
                    "role": str(row['Role']) if not pd.isna(row['Role']) else "",
                    "location": str(row['Location']) if not pd.isna(row['Location']) else "",
                    "company_activity": str(row['companyActivity']) if not pd.isna(row['companyActivity']) else "",
                    "task": str(row['Task']) if not pd.isna(row['Task']) else "",
                    "hours_saved": hours_saved,
                    "money_saved": money_saved
                }
            }
            records.append(record)
            
            # Progress reporting
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1} records...")
            
            # Add small delay to respect rate limits
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
                namespace="agents-namespace"
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
            result = index.fetch(ids=[record["id"]], namespace="agents-namespace")
            print(f"Record {record['id']}: {result}")
        except Exception as e:
            print(f"Error fetching record {record['id']}: {e}")

if __name__ == "__main__":
    upsert_to_pinecone()