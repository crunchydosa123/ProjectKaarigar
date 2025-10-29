# filename: firestore_users_crud.py

import os
from google.cloud import firestore

# ----------------------------
# Configuration
# ----------------------------
PROJECT_ID = "karigar-475215"  # Replace with your project ID
COLLECTION_NAME = "users"               # Collection inside the default DB

# ----------------------------
# Initialize Firestore Client
# ----------------------------
try:
    db = firestore.Client(project=PROJECT_ID)
    print("✅ Successfully initialized Firestore client.")
    print(f"Working with project: {db.project}\n")
except Exception as e:
    print("❌ Error initializing Firestore client. Make sure GOOGLE_APPLICATION_CREDENTIALS is set and valid.")
    print(f"Details: {e}")
    exit()

# ----------------------------
# CRUD Operations
# ----------------------------

def create_document(data, doc_id=None):
    """Adds a new document to the collection."""
    if doc_id:
        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
        doc_ref.set(data)
        print(f"✅ Document with ID '{doc_id}' created/updated.")
    else:
        _, doc_ref = db.collection(COLLECTION_NAME).add(data)
        print(f"✅ Document with auto-generated ID '{doc_ref.id}' created.")
        doc_id = doc_ref.id
    return doc_id

def get_document(doc_id):
    """Retrieves a single document by its ID."""
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        print(f"📄 Document '{doc_id}': {doc.to_dict()}")
        return doc.to_dict()
    else:
        print(f"❌ Document '{doc_id}' does not exist.")
        return None

def query_documents(field, operator, value):
    """Queries documents based on a field, operator, and value."""
    query = db.collection(COLLECTION_NAME).where(field, operator, value).stream()
    results = []
    for doc in query:
        print(f"📄 {doc.id} => {doc.to_dict()}")
        results.append(doc.to_dict())
    if not results:
        print("⚠️ No documents found matching the query.")
    return results

def update_document(doc_id, data_to_update):
    """Updates specific fields of an existing document."""
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
    doc_ref.update(data_to_update)
    print(f"✅ Document '{doc_id}' updated with {data_to_update}.")

def delete_document(doc_id):
    """Deletes a document by its ID."""
    db.collection(COLLECTION_NAME).document(doc_id).delete()
    print(f"✅ Document '{doc_id}' deleted.")

# ----------------------------
# Example Usage
# ----------------------------
if __name__ == "__main__":
    print("--- Starting Firestore CRUD operations ---\n")

    # 1️⃣ Create documents
    alice_id = create_document({
        "name": "Alice Wonderland",
        "email": "alice@example.com",
        "age": 30,
        "occupation": "Adventurer"
    })

    bob_id = create_document({
        "name": "Bob The Builder",
        "email": "bob@example.com",
        "age": 45,
        "occupation": "Construction Worker"
    }, doc_id="bob_the_builder")

    # 2️⃣ Get documents
    get_document(alice_id)
    get_document(bob_id)

    # 3️⃣ Query documents
    print("\n--- Query: age > 35 ---")
    query_documents("age", ">", 35)

    print("\n--- Query: occupation == 'Adventurer' ---")
    query_documents("occupation", "==", "Adventurer")

    # 4️⃣ Update a document
    update_document(alice_id, {"age": 31, "status": "Active"})
    get_document(alice_id)

    # 5️⃣ Delete a document
    delete_document(bob_id)
    get_document(bob_id)

    print("\n--- All operations completed ---")
