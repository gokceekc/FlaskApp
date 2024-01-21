from flask_ngrok import run_with_ngrok
from flask import Flask, render_template, request
from PIL import Image  # Import the Image class from PIL
from diffusers import StableDiffusionPipeline
import torch
import base64
from io import BytesIO
#from werkzeug.utils import secure_filename
from PIL import ImageDraw, ImageFont
from flask import send_file
from flask import redirect, url_for


global_generated_image = None
global_generated_poster = None


# Load model
pipe_img2img = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16)
pipe_img2img.to("cuda")



# Start flask app and set to ngrok
app = Flask(__name__, template_folder='.')
run_with_ngrok(app)

@app.route('/')
def initial():
    return render_template('index_img2img.html')

@app.route('/submit-poster', methods=['GET', 'POST'])
def generate_poster():
    global global_generated_image
    global global_generated_poster

    # Initialize button size before the conditional block
    button_size = (150, 50)  # Default size

    if request.method == 'POST':
        # Get the title from the form
        poster_title = request.form['poster-title']
        button_text = request.form['button-text']

        # Check if global_generated_image is set
        if global_generated_image:
            # Convert the base64 image string to PIL image
            generated_image = Image.open(BytesIO(base64.b64decode(global_generated_image.split(',')[1])))

            # Create a blank poster image
            poster_width, poster_height = 800, 1000
            poster = Image.new("RGB", (poster_width, poster_height), "white")
            draw = ImageDraw.Draw(poster)

            # Adjust the location and size of the generated image on the poster
            generated_image_size = (300, 300)  # Adjust the size of the generated image
            generated_image_position = (250, 300)  # Adjust the position of the generated image
            poster.paste(generated_image.resize(generated_image_size), generated_image_position)

            # Adjust the location and size of the logo on the poster
            logo_input = request.files['logo-input']
            logo_img = Image.open(logo_input).convert("RGBA")

            logo_size = (200, 100)  # Adjust the size of the logo
            logo_position = (300, 100)  # Adjust the position of the logo
            logo_img = logo_img.resize(logo_size)

            # Paste the logo onto the poster
            poster.paste(logo_img, logo_position, logo_img)

            # Adjust the location and size of the headline on the poster
            font_size_headline = 50  # Adjust the font size for the headline
            font_path_headline = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"  # Replace with the path to your TrueType font file
            font_headline = ImageFont.truetype(font_path_headline, font_size_headline)

            # Adjust the location and size of the button on the poster
            font_size_button = 20  # Adjust the font size for the button text
            font_button = ImageFont.truetype(font_path_headline, font_size_button)

              # Adjust the location and size of the button on the poster
            font_size_button = 20  # Adjust the font size for the button text
            font_button = ImageFont.truetype(font_path_headline, font_size_button)

            # Calculate the x-coordinate to keep the button centered on the x-axis
            button_text_size = font_button.getsize(button_text)
            button_x = (poster_width - button_text_size[0]) // 2

            # Adjust the y-coordinate to place the button at the desired position
            button_y = 750  # You can change this to the desired y-coordinate

            button_size = (button_text_size[0] + 20, button_text_size[1] + 20)  # Add some padding to the size

            # Draw the button with the specified text using the button font
            draw.rectangle([button_x, button_y, button_x + button_size[0], button_y + button_size[1]], outline="black")
            text_x = button_x + (button_size[0] - button_text_size[0]) // 2
            text_y = button_y + (button_size[1] - button_text_size[1]) // 2
            draw.text((text_x, text_y), button_text, font=font_button, fill="black")

            # Get the width of the text before drawing
            text_width, text_height = draw.textsize(poster_title, font_headline)

            # Adjust the coordinates where the text is drawn
            text_x = (poster_width - text_width) // 2
            text_y = 650

            draw.text((text_x, text_y), poster_title, font=font_headline, fill="black")

            # Save the poster image
            poster_path = "/content/app/static/poster.png"
            poster.save(poster_path)

            # Convert the poster image to base64 for display
            buffered = BytesIO()
            poster.save(buffered, format="PNG")
            poster_str = base64.b64encode(buffered.getvalue())
            global_generated_poster = "data:image/png;base64," + str(poster_str)[2:-1]

            return render_template('index_img2img.html', generated_image=global_generated_image, poster_image=global_generated_poster)

    # Render the form for poster title
    return render_template('index_img2img.html', generated_image='', poster_image='')


@app.route('/submit-img2img', methods=['POST'])
def generate_image_img2img():

    # Handle uploaded image
    uploaded_image = request.files['image-input']


    # Check if the file is allowed based on its extension (you can customize this)
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' in uploaded_image.filename and uploaded_image.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
        image = Image.open(uploaded_image).convert("RGB")
        image = image.resize((768, 512))

        # Get text prompt from the form
        prompt = request.form['prompt-input']

        # Generate image-to-image transformation
        output_images = pipe_img2img(prompt=prompt, image=image, strength=0.75, guidance_scale=7.5).images
        output_image = output_images[0]

        # Convert the generated image to base64 for display
        buffered = BytesIO()
        output_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        generated_image_data = "data:image/png;base64," + str(img_str)[2:-1]


            # Save the generated image data to a global variable
        global global_generated_image
        global_generated_image = generated_image_data

        # Set a flag to make the poster form visible in the HTML
        poster_form_visible = True

        # Return a response with the generated image data and make the poster form visible
        return render_template('index_img2img.html', generated_image=global_generated_image, poster_form_visible=poster_form_visible)

app.run()



