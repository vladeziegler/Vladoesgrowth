import os
import weaviate

from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure

wcd_url = os.getenv("WEAVIATE_URL")
wcd_api_key = os.getenv("WEAVIATE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")


def generate_chunks_and_metadata(file_path):
    document_converter = DocumentConverter()
    chunker = HybridChunker(
        tokenizer="sentence-transformers/all-MiniLM-L6-v2",
    )
    source = Path(file_path)
    converted_documented = document_converter.convert(source).document
    chunk_iterable = chunker.chunk(converted_documented)

    chunk_info = extract_chunk_info(chunk_iterable)
    for index, chunk in enumerate(chunk_info):
        print(f"Chunk {index + 1}:")
        print(f"Text: {chunk['text']}")
        print(f"Metadata: {chunk['metadata']}")
        print("-" * 50)

    return chunk_info


def extract_chunk_info(chunks):
    results = []

    for chunk in chunks:
        if isinstance(chunk.text, str) and "=" in chunk.text:
            # Split the text by periods to separate entries
            entries = chunk.text.split(". ")

            for entry in entries:
                # Skip empty entries
                if not entry.strip():
                    continue

                # Parse entry data
                parts = entry.split(" = ")
                if len(parts) == 2:
                    identifier, value = parts

                    # Add error handling for identifier splitting
                    try:
                        # First try comma with space
                        if ", " in identifier:
                            row_id, col_id = identifier.split(", ")
                        # Then try just comma
                        elif "," in identifier:
                            row_id, col_id = identifier.split(",")
                        else:
                            # print(f"Skipping malformed identifier: {identifier}")
                            continue

                        # Clean up any whitespace
                        row_id = row_id.strip()
                        col_id = col_id.strip()

                        # Initialize or get existing entry
                        current_entry = next(
                            (x for x in results if x.get("row_id") == row_id), None
                        )
                        if not current_entry:
                            current_entry = {
                                "row_id": row_id,
                                "metadata": {
                                    "company_activity": None,
                                    "task": None,
                                    "location": None,
                                    "role": None,
                                    "hours_saved": None,
                                    "money_saved": None,
                                },
                                "text": {},
                            }
                            results.append(current_entry)

                        # Map values to appropriate fields
                        col_mapping = {
                            "1": ("metadata", "role"),
                            "2": ("metadata", "location"),
                            "3": ("metadata", "company_activity"),
                            "4": ("metadata", "task"),
                            "5": ("metadata", "hours_saved"),
                            "6": ("metadata", "money_saved"),
                        }

                        text_fields = {
                            "5": "money_saved",
                            "6": "hours_saved",
                        }

                        if col_id in col_mapping:
                            section, field = col_mapping[col_id]
                            current_entry[section][field] = value
                        elif col_id in text_fields:
                            current_entry["text"][text_fields[col_id]] = value

                    except ValueError as e:
                        print(f"Error processing entry: {entry}")
                        print(f"Error details: {e}")
                        continue

    # Clean up results
    final_results = []
    for entry in results:
        if isinstance(entry.get("text"), dict) and entry["text"].get("title"):
            final_results.append(entry)

    return final_results


# if __name__ == "__main__":
#     data = generate_chunks_and_metadata(
#     )
#     print("data", data)

if __name__ == "__main__":
    data = generate_chunks_and_metadata(
        file_path="/Users/vladimirdeziegler/text_crewai/Vladoesgrowth/RecommendationEngine/sources/agents_data.xlsx"
    )
    print("data", data)
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=wcd_url,
        auth_credentials=Auth.api_key(wcd_api_key),
        headers={"X-OpenAI-Api-Key": openai_api_key},
    )
    print("client ready", client.is_ready())  # Should print: `True`
    if client.is_ready():
        netflix_data = client.collections.create(
            name="agents_data",
            vectorizer_config=Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small",
            ),
            generative_config=Configure.Generative.openai(
                model="gpt-4o-mini",
            ),
        )

        with netflix_data.batch.dynamic() as batch:
            for d in data:
                batch.add_object(
                    {
                        
                        "company_activity": d["metadata"]["company_activity"],
                        "task": d["metadata"]["task"],
                        "location": d["metadata"]["location"],
                        "role": d["metadata"]["role"],
                        "hours_saved": d["metadata"]["hours_saved"],
                        "money_saved": d["metadata"]["money_saved"],
                    }
                )
        print("successfully added in docs")
        client.close()

    else:
        print("client is not ready")
