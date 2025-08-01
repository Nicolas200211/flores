from flask import Flask, send_file, render_template_string
import turtle as tu
import re
import docx
import io
from PIL import Image, ImageDraw
import base64
import math

app = Flask(__name__)

def create_flower():
    # Tu código original para generar el dibujo
    source = "tulipanes_actualizado"
    data = docx.Document(f"{source}.docx")
    coordinates = []
    colour = []

    for i in data.paragraphs:
        try:
            coord_stg_tup = re.findall(r'\([-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)?\)', i.text)
            coord_num_tup = []
            color_stg_tup = re.findall(r'\([-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)?\)', i.text)
            color_val = re.findall(r'[-+]?\d*\.\d*', color_stg_tup[0])
            color_val_lst = [float(k) for k in color_val]
            colour.append(tuple(color_val_lst))

            for j in coord_stg_tup:
                coord_pos = re.findall(r'[-+]?\d*\.\d*', j)
                coord_num_lst = [float(k) for k in coord_pos]
                coord_num_tup.append(tuple(coord_num_lst))

            coordinates.append(coord_num_tup)
        except:
            pass

    # Crear una imagen directamente con Pillow
    width, height = 800, 600
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Dibujar las flores
    for i in range(len(coordinates)):
        if len(coordinates[i]) < 2:
            continue
            
        # Convertir coordenadas para Pillow
        points = []
        for x, y in coordinates[i]:
            # Ajustar las coordenadas al centro de la imagen
            px = int(x * 2 + width/2)
            py = int(-y * 2 + height/2)  # Invertir Y para que sea como en turtle
            points.append((px, py))
        
        # Dibujar la línea
        if len(points) > 1:
            try:
                color = colour[i % len(colour)]
                # Asegurarse de que el color esté en el rango 0-255 y sea una tupla de 3 valores
                if isinstance(color, (list, tuple)) and len(color) >= 3:
                    r = min(255, max(0, int(color[0] * 255)))
                    g = min(255, max(0, int(color[1] * 255)))
                    b = min(255, max(0, int(color[2] * 255)))
                    draw.line(points, fill=(r, g, b), width=2)
            except Exception as e:
                print(f"Error dibujando línea: {e}")
                # Usar color rojo como respaldo
                draw.line(points, fill=(255, 0, 0), width=2)
    
    # Guardar la imagen
    img.save('flor.png')
    return 'flor.png'

@app.route('/')
def index():
    # Generar la imagen
    image_path = create_flower()
    
    # Leer la imagen y mostrarla
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flores para ti</title>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                height: 100vh;
                margin: 0;
                background-color: #f0f8ff;
                font-family: Arial, sans-serif;
            }}
            img {{
                max-width: 90%;
                max-height: 80vh;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);
                margin-bottom: 20px;
            }}
            h1 {{
                color: #ff69b4;
                margin-bottom: 20px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>¡Estas flores son para ti! 💐</h1>
        <img src="/flor" alt="Flores dibujadas con Python">
    </body>
    </html>
    """

@app.route('/flor')
def get_flower():
    return send_file('flor.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
