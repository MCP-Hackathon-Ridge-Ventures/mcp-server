PROMPT = """
{prompt}

User Request (App to Generate):

{user_request}

Return your code ONLY in the following format (strictly):

{format_instructions}
"""

EDITOR_PROMPT = """
{prompt}

You had already generated the app code. 
But the user has requested some changes to the app.

User Request (Changes to the app):

{user_request}

Previous App Code:
{previous_app_code}

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


METADATA_EDITOR_PROMPT = """
You are an expert in generating metadata for React apps.

Your Task:
Generate metadata for the app. 
You had already generated the app metadata.
But the user has requested some changes to the app.

Notes:
    •    Only generate metadata for the app. Do not generate any other text.
    •    You are not responsible for generating the app code.
    
User Request (Changes to the app):

{user_request}

Previous App Metadata:
{previous_app_metadata}

{format_instructions}
"""
