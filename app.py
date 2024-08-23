import streamlit as st
from transformers import Blip2Processor, BlipForConditionalGeneration, pipeline
from PIL import Image, UnidentifiedImageError
import requests
from io import BytesIO
import torchvision.transforms as transforms


# Load the pre-trained models
@st.cache_resource
def load_models():
    processor = Blip2Processor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )
    emotion_analyzer = pipeline(
        "text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion"
    )
    return processor, model, emotion_analyzer


processor, model, emotion_analyzer = load_models()

# Generate Image Description


def generate_description(image_url, max_length=100, max_image_size=(512, 512)):

    try:
        response = requests.get(image_url)
        response.raise_for_status()

        # Ensure the content is actually an image
        image = Image.open(BytesIO(response.content)).convert("RGB")

        # Resize if necessary
        if image.width > max_image_size[0] or image.height > max_image_size[1]:
            image = image.resize(max_image_size, Image.LANCZOS)

        # Preprocess the image with padding and max length
        inputs = processor(
            images=image, return_tensors="pt", padding=True, max_length=max_length
        )

        # Move the inputs to the same device as the model
        inputs = {key: value.to(model.device) for key, value in inputs.items()}

        # Generate the description
        outputs = model.generate(**inputs)
        description = processor.decode(outputs[0], skip_special_tokens=True)

        return description

    except UnidentifiedImageError:
        st.error(
            "The provided URL does not point to a valid image. Please check the URL."
        )

        return None

    except requests.exceptions.RequestException as e:

        st.error(f"Failed to fetch the image from the URL: {e}")

        return None


# Analyze Emotional Tone
def analyze_emotion(description):

    emotions = emotion_analyzer(description)
    return emotions[0]["label"]


# Streamlit Interface
st.title("Sri's Image Analyzer with CNN for SA")

image_url = st.text_input("Enter the Image URL:")

if st.button("Analyze"):
    if image_url:
        with st.spinner("Generating description..."):
            description = generate_description(image_url)

        if description:  # Proceed only if a valid description is generated
            with st.spinner("Analyzing emotional tone..."):
                emotion = analyze_emotion(description)

            st.image(image_url, caption="Input Image", use_column_width=True)
            st.write(f"**Description:** {description}")
            st.write(f"**Emotional Tone:** {emotion}")
    else:
        st.error("Please enter a valid image URL.")

# Example Section
st.sidebar.title("Example URLs")
st.sidebar.write("Try these examples:")
st.sidebar.write("1. https://images.unsplash.com/photo-1503023345310-bd7c1de61c7d")
st.sidebar.write("2. https://images.unsplash.com/photo-1533236899715-8d7c1de64f1f")
st.sidebar.write("3. https://images.unsplash.com/photo-1541698444083-023c97d3f4b6")
