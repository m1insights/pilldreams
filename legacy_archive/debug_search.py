
from ddgs import DDGS
import json

def test_search():
    print("Testing DuckDuckGo Search Backends...")
    query = "Viking Therapeutics (VKTX) investor relations pipeline corporate overview"
    
    # Test 'api' backend
    print("\n--- Testing 'api' backend ---")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3, backend="api"))
            print(f"Found {len(results)} results")
            for r in results:
                print(f"- {r['title']}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 'html' backend
    print("\n--- Testing 'html' backend ---")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3, backend="html"))
            print(f"Found {len(results)} results")
            for r in results:
                print(f"- {r['title']}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 'lite' backend
    print("\n--- Testing 'lite' backend ---")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3, backend="lite"))
            print(f"Found {len(results)} results")
            for r in results:
                print(f"- {r['title']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search()
