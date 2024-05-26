import pandas as pd
from PIL import Image
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from pathlib import Path
from io import BytesIO
import base64
import cv2
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageChops
import os 
import subprocess

def apply_inverse_mask(original_image, mask_image):
    "return the masked images"
    original_image_resized = original_image.resize(mask_image.size)

    white_image = Image.new('RGB', mask_image.size, (255, 255, 255))

    # Invert the mask image
    inverted_mask = ImageChops.invert(mask_image)

    # Paste the original image onto the new white image based on the inverted mask
    white_image.paste(original_image_resized, mask=inverted_mask)

    return white_image

def save_uploaded_image(uploaded_file, save_path):
   
    try:
        image = Image.open(uploaded_file)
        image.save(save_path)
    except Exception as e:
        return st.error(f"Error saving file: {e}")




def run_command(command):
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")

command = [
    "python", "test.py",
    "--model", "2",
    "--checkpoints", "checkpoints/places2",
    "--input", "temp/images",
    "--mask", "temp/masks",
    "--output", "output"
]




drawing_mode = st.sidebar.selectbox(
    "Drawing tool:", ("freedraw", "line", "rect", "circle", "transform")
)

stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 25)
if drawing_mode == 'point':
    point_display_radius = st.sidebar.slider("Point display radius: ", 1, 25, 3)
stroke_color = st.sidebar.color_picker("Stroke color hex: ","#eee")
bg_color = st.sidebar.color_picker("Background color hex: ", "#000000")
bg_image = st.sidebar.file_uploader("Background image:", type=["png"])


if bg_image is not  None:
    imagex = Image.open(bg_image)
    save_directory = "to_process/"
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    save_path = os.path.join(save_directory, bg_image.name)
    
    save_uploaded_image(bg_image, save_path)


realtime_update = st.sidebar.checkbox("Update in realtime", True)

    
global background_image
# Create a canvas component
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    background_image=Image.open(bg_image) if bg_image else None,
    update_streamlit=realtime_update,
    height=400,
    width = 400,
    drawing_mode=drawing_mode,
    point_display_radius=point_display_radius if drawing_mode == 'point' else 0,
    key="canvas",
)

try:
    Path("temp/").mkdir()
except FileExistsError:
    pass


if canvas_result.image_data is not None:
    st.image(canvas_result.image_data,caption= "mask",output_format="JPEG")

data = canvas_result

if data is not None and data.image_data is not None:
    img_data = data.image_data
    im = Image.fromarray(img_data.astype("uint8"), mode="RGBA")
    im.save("temp/masks/mask_temp.png", "PNG")
    buffered = BytesIO()
    im.save(buffered, format="PNG")
    img_data = buffered.getvalue()
    try:
            # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(img_data.encode()).decode()
    except AttributeError:
        b64 = base64.b64encode(img_data).decode()

on = st.toggle("Start the Patching Image")

if on:
    st.write("Patching the image ")
    image_xx = Image.open("to_process/"+bg_image.name)
    image_yy = Image.open("temp/masks/mask_temp.png")
    result_image = apply_inverse_mask(image_xx, image_yy)
    result_image.save("temp/images/mask_temp.png")

    st.image("temp/images/mask_temp.png")


on = st.toggle("Process and Download Data")
if on:
    
    run_command(command)
    image = cv2.imread("output/mask_temp.png")
    bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    # bgr_image=cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    cv2.imwrite("output/mask_temp.png",bgr_image)
    
    st.image("output/mask_temp.png")
    with open("output/mask_temp.png", "rb") as file:
        btn = st.download_button(
                label="Final image",
                data=file,
                file_name="mask_temp.png",
                mime="image/png"
            )

        
    