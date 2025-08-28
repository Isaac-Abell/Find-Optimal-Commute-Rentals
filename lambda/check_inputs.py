import json

VALID_COMMUTE_TYPES = ['driving', 'bicycling', 'walking', 'transit']
VALID_SORT_BY = [
    'list_price', 'beds', 'baths', 'distance', 'commute_seconds', 'commute_time'
]

def check_inputs(event):
    """
    Validates user inputs for listings queries.

    Parameters:
        event (dict): Input dictionary containing user request fields.

    Returns:
        dict: Cleaned inputs with defaults applied.
    """
    # Normalize event structure
    if 'body' in event and isinstance(event['body'], str):
        event = json.loads(event['body'])
    elif 'body' in event and isinstance(event['body'], dict):
        event = event['body']

    # Ensures Required Fields are provided
    if 'user_address' not in event or not isinstance(event['user_address'], str):
        raise ValueError("user_address is required and must be a string")
    user_address = event['user_address']

    # Gets and validates commute types
    commute_type = event.get('commute_type', 'walking').lower()
    if commute_type not in VALID_COMMUTE_TYPES:
        raise ValueError(f"commute_type must be one of {VALID_COMMUTE_TYPES}")

    # Gets and validates Pagination Info
    try:
        page = int(event.get('page', 1))
    except (TypeError, ValueError):
        raise ValueError("page must be an integer")
    if page < 1:
        raise ValueError("page must be >= 1")

    # Gets and validates page_size
    try:
        page_size = int(event.get('page_size', 20))
    except (TypeError, ValueError):
        raise ValueError("page_size must be an integer")
    if page_size < 1 or page_size > 50:
        raise ValueError("page_size must be between 1 and 50")

    # Gets and validates filters
    filters = event.get('filters', {})
    if not isinstance(filters, dict):
        raise ValueError("filters must be a dictionary")

    # Gets and validates sort_by
    sort_by = event.get('sort_by', 'list_price')
    if sort_by not in VALID_SORT_BY:
        raise ValueError(f"sort_by must be one of {VALID_SORT_BY}")

    # Gets and validates ascending
    ascending = event.get('ascending', True)
    if not isinstance(ascending, bool):
        raise ValueError("ascending must be a boolean")

    # Ensures all fields are included in the returned dictionary
    return {
        "user_address": user_address,
        "commute_type": commute_type,
        "page": page,
        "page_size": page_size,
        "filters": filters,
        "sort_by": sort_by,
        "ascending": ascending,
    }