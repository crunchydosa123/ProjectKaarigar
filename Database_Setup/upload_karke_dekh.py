from google.cloud import storage

# Instantiate a client
# The client automatically picks up credentials from GOOGLE_APPLICATION_CREDENTIALS
# or gcloud CLI if available.
client = storage.Client()

# Replace with your bucket name
bucket_name = "all_in_one_bucket"
bucket = client.bucket(bucket_name)

# --- Upload a file ---
def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

# Example usage:
# with open("local_test_file.txt", "w") as f:
#     f.write("Hello from Google Cloud Storage!")
# upload_blob("local_test_file.txt", "my-first-object.txt")

# --- Download a file ---
def download_blob(source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")

# Example usage:
# download_blob("my-first-object.txt", "downloaded_test_file.txt")

# --- List all objects in a bucket ---
def list_blobs():
    """Lists all the blobs in the bucket."""
    blobs = client.list_blobs(bucket_name)
    print("Blobs in bucket:")
    for blob in blobs:
        print(blob.name)

# Example usage:
# list_blobs()

# --- Delete an object ---
def delete_blob(blob_name):
    """Deletes a blob from the bucket."""
    blob = bucket.blob(blob_name)
    blob.delete()
    print(f"Blob {blob_name} deleted.")

# Example usage:
# delete_blob("my-first-object.txt")
upload_blob("/Users/prathamgadkari/Hackathons/Google GenAI Exchange Hackathon/ProjectKaarigar/dialogue_example.mp4", "videos/abcabcabc")

