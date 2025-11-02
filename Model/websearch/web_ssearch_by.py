import requests
import json

def google_search(search_term, api_key, cx_id, num_results=10):
    """
    Performs a Google search using the Custom Search JSON API.

    Args:
        search_term (str): The query you want to search for.
        api_key (str): Your Google API Key. (NOT a service account)
        cx_id (str): Your Programmable Search Engine ID (CX ID).
        num_results (int): The number of results to return (1-10).

    Returns:
        dict: The JSON response from the API, or None if an error occurred.
    """
    
    # The base URL for the Custom Search JSON API
    url = "https://www.googleapis.com/customsearch/v1"
    
    # Set up the query parameters
    params = {
        'key': api_key,
        'cx': cx_id,
        'q': search_term,
        'num': num_results
    }
    
    try:
        # Make the GET request
        response = requests.get(url, params=params)
        
        # Raise an exception if the request was unsuccessful
        response.raise_for_status()
        
        # Parse the JSON response
        return response.json()
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        try:
            # Try to print the specific error message from Google
            error_message = response.json().get('error', {}).get('message')
            print(f"API Error: {error_message}")
        except json.JSONDecodeError:
            print("Could not decode error response.")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    
    return None

# --- --- --- --- --- --- --- --- --- ---
# HOW TO USE THIS SCRIPT
# --- --- --- --- --- --- --- --- --- ---
if __name__ == "__main__":
    
    # 1. --- GET YOUR API KEY ---
    # This is NOT your service account file.
    # Go to: https://console.cloud.google.com/apis/credentials
    # Click "+ CREATE CREDENTIALS" -> "API key".
    # Copy the key string (starts with "AIza...").
    # You MUST also enable the "Custom Search JSON API" in the Library.
    API_KEY = ""  # TODO: Set your Google API Key

    # 2. --- GET YOUR SEARCH ENGINE ID (CX ID) ---
    # Go to: https://programmablesearchengine.google.com/
    # Click "Add" to create a new search engine.
    # In the setup, toggle on "Search the entire web".
    # After creating it, copy the "Search engine ID" from the overview page.
    CX_ID = ""  # TODO: Set your Custom Search Engine ID
    
    # 3. --- SET YOUR QUERY ---
    QUERY = "What is the YouTube Analytics API?"

    if API_KEY == "YOUR_API_KEY_HERE" or CX_ID == "YOUR_CX_ID_HERE":
        print("Error: Please replace 'YOUR_API_KEY_HERE' and 'YOUR_CX_ID_HERE' with your actual credentials.")
        print("See the comments in the code for instructions on how to get them.")
    else:
        # Perform the search
        search_results = google_search(QUERY, API_KEY, CX_ID, num_results=5)
        
        if search_results:
            print(f"--- Search results for '{QUERY}' ---")
            
            # Check if 'items' (the results list) exists in the response
            if 'items' in search_results:
                for i, item in enumerate(search_results['items']):
                    print(f"\nResult #{i + 1}:")
                    print(f"  Title: {item.get('title')}")
                    print(f"  Snippet: {item.get('snippet').replace(chr(10), ' ')}")
                    print(f"  Link: {item.get('link')}")
            else:
                print("No results found for your query.")
        else:
            print("Search failed.")

