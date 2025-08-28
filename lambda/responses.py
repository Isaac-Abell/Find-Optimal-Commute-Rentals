"""
responses.py
------------
Utility functions for building successful and error responses for AWS Lambda.
"""

import json


def build_response(results, page, page_size, total):
    """
    Build a successful Lambda response.

    Args:
        results (list): Listing results.
        page (int): Current page.
        page_size (int): Number of listings per page.
        total (int): Total number of listings.

    Returns:
        dict: JSON Lambda response.
    """
    return {
        "statusCode": 200,
        "body": json.dumps({
            "page": page,
            "page_size": page_size,
            "total_listings": total,
            "results": results
        })
    }


def build_error_response(message, status_code):
    """
    Build an error Lambda response.

    Args:
        message (str): Error message.
        status_code (int): HTTP status code.

    Returns:
        dict: JSON Lambda error response.
    """
    return {
        "statusCode": status_code,
        "body": json.dumps({"error": message})
    }