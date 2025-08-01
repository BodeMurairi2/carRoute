# get_car_info.py

import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Load environment variables
load_dotenv('auth.env')

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_request(image_path):
    """Send image + prompt to Gemini, return structured Python dict or None if failed."""
    try:
        # Load image
        image = Image.open(image_path)

        # Initialize Gemini vision model
        model = genai.GenerativeModel(model_name=os.getenv("GEMINI_AI_MODEL"))

        # Prompt Gemini for structured JSON
        prompt = (
            "About this image: First, tell me if it's a car or not. "
            "If it is a car, return a JSON object with this structure: "
            "{ "
                "\"is_car\": true, "
                "\"car_details\": { "
                    "\"brand\": string, "
                    "\"model\": string, "
                    "\"approximate_year\": string, "
                    "\"body_style\": string, "
                    "\"exterior_design\": string, "
                    "\"interior_design\": string, "
                    "\"color\": string, "
                    "\"lights\": string, "
                    "\"wheels\": string, "
                    "\"technology\": string, "
                    "\"price_range\": string, "
                    "\"where_to_buy\": string, "
                    "\"car_features\": [string, ...], "
                    "\"engine_type\": string, "
                    "\"performance_specifications\": { "
                        "\"horsepower\": string, "
                        "\"torque\": string, "
                        "\"0_60_mph\": string, "
                        "\"top_speed\": string "
                    "}, "
                    "\"safety_features\": [string, ...], "
                    "\"image_url_info\": string, "
                    "\"special_features_modifications\": string "
                "} "
            "}. "
            "If it’s NOT a car, return: "
            "{ "
                "\"is_car\": false, "
                "\"image_url_info\": string "
            "}. Only return valid JSON. No extra explanation."
        )

        # Send image and prompt to Gemini
        response = model.generate_content([prompt, image])
        raw_text = response.text.strip()

        # Extract only the JSON part using regex
        json_match = re.search(r'\{[\s\S]+\}', raw_text)
        if not json_match:
            print("No valid JSON found in Gemini response.")
            print(raw_text)
            return None

        json_text = json_match.group()

        # Parse the JSON text
        data = json.loads(json_text)

        # Normalize "is_car" to boolean if needed
        if isinstance(data.get("is_car"), str):
            data["is_car"] = data["is_car"].strip().lower() == "true"

        # If it's not a car, make sure only minimal structure is returned
        if not data.get("is_car", False):
            return {
                "is_car": False,
                "image_url_info": data.get("image_url_info", "No image info provided")
            }

        # Else, it's a car – return full structure
        return data

    except json.JSONDecodeError as je:
        print(f"JSON parsing error: {je}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    image_path = "/home/bode-murairi/Pictures/car/images.jpeg"
    result = get_request(image_path)
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Failed to get a valid response from Gemini.")
