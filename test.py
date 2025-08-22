import requests

# --- Global API URL ---

def test_api_basic():
    event = {
        "user_address": "20 West 34th Street, NY",
        "commute_type": "WALK",
        "page": 1,
        "page_size": 5,
        "filters": {},
        "sort_by": "list_price",
        "ascending": True
    }
    response = requests.post(API_URL, json=event)
    assert response.status_code == 200
    result = response.json()
    assert "results" in result
    print("test_api_basic passed!")

def test_api_with_filters():
    event = {
        "user_address": "20 West 34th Street, NY",
        "filters": {"min_price": 1500, "max_price": 2500, "min_beds": 2},
        "sort_by": "list_price",
        "ascending": False,
        "page": 1,
        "page_size": 5
    }
    response = requests.post(API_URL, json=event)
    assert response.status_code == 200
    result = response.json()
    assert "results" in result
    print("test_api_with_filters passed!")

def test_api_pagination():
    event_page1 = {
        "user_address": "20 West 34th Street, NY",
        "page": 1,
        "page_size": 5,
        "sort_by": "list_price"
    }
    event_page2 = {
        "user_address": "20 West 34th Street, NY",
        "page": 2,
        "page_size": 5,
        "sort_by": "list_price"
    }
    response1 = requests.post(API_URL, json=event_page1)
    response2 = requests.post(API_URL, json=event_page2)
    assert response1.status_code == 200
    assert response2.status_code == 200
    result1 = response1.json()
    result2 = response2.json()
    assert result1["results"] != result2["results"]
    print("test_api_pagination passed!")

def test_api_distance_and_commute():
    event = {
        "user_address": "20 West 34th Street, NY",
        "page": 1,
        "page_size": 5
    }
    response = requests.post(API_URL, json=event)
    assert response.status_code == 200
    result = response.json()
    for listing in result["results"]:
        assert "distance_meters" in listing
        assert listing["distance_meters"] >= 0
        assert "commute_minutes" in listing
        assert listing["commute_minutes"] >= 0
    print("test_api_distance_and_commute passed!")

# --- Run tests directly ---
if __name__ == "__main__":
    test_api_basic()
    test_api_with_filters()
    test_api_pagination()
    test_api_distance_and_commute()
    print("All API integration tests passed!")