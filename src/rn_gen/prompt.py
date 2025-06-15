PROMPT = """
{prompt}

User Request (App to Generate):

{user_request}

Return your code ONLY in the following format (strictly):

{format_instructions}
"""

METADATA_PROMPT = """

You are an expert in generating metadata for React apps.

Your Task:
Generate metadata for the app. You are given a user request of someone wanting to build an app. Your job is to generate metadata for the app.

Notes:
    •    Only generate metadata for the app. Do not generate any other text.
    •    You are not responsible for generating the app code.
    
User Request:
{user_request}

{format_instructions}
"""
