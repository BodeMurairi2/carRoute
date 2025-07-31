import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Load environment variables
load_dotenv('auth.env')

# Configure your Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_request(image_path):
    """Send an image + prompt to Gemini and get JSON info about car"""
    
    # Load image using PIL
    image = Image.open(image_path)

    # Initialize Gemini model (must be multimodal)
    model = genai.GenerativeModel(model_name=os.getenv("GEMINI_AI_MODEL", "gemini-pro-vision"))

    # Define your prompt
    prompt = (
        "About this image: First, tell me if it's a car or not. "
        "If it is a car, return a JSON object with the following consistent structure: "
        "{ "
            "\"is_car\": true, "
            "\"car_details\": { "
                "\"brand\": string, "
                "\"model\": string, "
                "\"approximate_year\": string,"
                "\"body_style\": string, "
                "\"exterior_design\": string, "
                "\"interior_design\": string, "
                "\"color\": string, "
                "\"lights\": string, "
                "\"wheels\": string, "
                "\"technology\": string, "
                "\"price_range\": string, "
                "\"where_to_buy\": string, "
                "\"car_features\": [string, string, ...], "
                "\"engine_type\": string, "
                "\"performance_specifications\": { "
                    "\"horsepower\": string, "
                    "\"torque\": string, "
                    "\"0_60_mph\": string, "
                    "\"top_speed\": string "
                "}, "
                "\"safety_features\": [string, string, ...], "
                "\"image_url_info\": string, "
                "\"special_features_modifications\": string "
            "} "
        "}. "
        "If the image is NOT a car, return this JSON object instead: "
        "{ "
            "\"is_car\": false, "
            "\"image_url_info\": string "
        "}. Only return raw JSON with no explanation or markdown formatting."
    )

    # Call Gemini
    response = model.generate_content([prompt, image])
    print(response.text)
    return response.text

if __name__ == "__main__":
    # Example usage
    image_path = "/home/bode-murairi/Pictures/car/images.jpeg"
    response_text = get_request(image_path)
    print(response_text)  # This will print the JSON response from Gemini
