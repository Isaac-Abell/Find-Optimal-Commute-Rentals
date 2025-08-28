"""
lambda_handler.py
-----------------
Entry point for AWS Lambda that fetches property listings near a user-provided address,
computes commute times, and returns paginated JSON results.

Modules used:
- input_validation (for event validation)
- geocoding (for address geocoding and city validation)
- listings (for fetching and formatting listings)
"""

from check_inputs import check_inputs
from geocoding import geocode_user_address, validate_city
from listings import get_listings_with_commute
from responses import build_response, build_error_response


def lambda_handler(event, context):
    """
    AWS Lambda handler to process a property listing request.

    Args:
        event (dict): Contains user inputs such as address, filters, sorting, and commute type.
        context: AWS Lambda context object (unused).

    Returns:
        dict: JSON response with listings, commute times, and pagination.
    """
    try:
        validated = check_inputs(event)
        user_lat, user_lon = geocode_user_address(validated['user_address'])
        closest_city = validate_city(user_lat, user_lon)

        results, total = get_listings_with_commute(
            user_coords=(user_lat, user_lon),
            closest_city=closest_city,
            filters=validated['filters'],
            sort_by=validated['sort_by'],
            ascending=validated['ascending'],
            page=validated['page'],
            page_size=validated['page_size'],
            commute_type=validated['commute_type']
        )

        return build_response(results, validated['page'], validated['page_size'], total)

    except ValueError as ve:
        return build_error_response(str(ve), 400)
    except Exception as e:
        print(f"Unhandled error: {e}")
        return build_error_response("Internal server error", 500)