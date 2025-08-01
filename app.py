from flask import Flask, send_file, render_template_string, Response
import re
import docx
import io
import base64
import math
import matplotlib
matplotlib.use('Agg')  # Para usar sin interfaz gráfica
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

app = Flask(__name__)

def create_flower():
    # Leer el documento con las coordenadas
    source = "tulipanes_actualizado"
    data = docx.Document(f"{source}.docx")
    coordinates = []
    colours = []

    for paragraph in data.paragraphs:
        try:
            # Extraer coordenadas
            coord_stg_tup = re.findall(
                r'\(([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)\)', 
                paragraph.text
            )
            
            # Extraer colores
            color_stg_tup = re.findall(
                r'\(([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)\)', 
                paragraph.text
            )
            
            if not coord_stg_tup or not color_stg_tup:
                continue
                
            # Convertir coordenadas a números
            coord_num_tup = [(float(x), float(y)) for x, y in coord_stg_tup]
            
            # Convertir colores a tuplas de float
            color_val = [float(x) for x in color_stg_tup[0]]
            colours.append(tuple(color_val))
            coordinates.append(coord_num_tup)
            
        except Exception as e:
            print(f"Error procesando párrafo: {e}")
            continue
            pass

    # Crear una figura de Matplotlib
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    ax.axis('off')  # Ocultar ejes
    
    # Encontrar límites para escalar correctamente
    all_points = [point for sublist in coordinates for point in sublist if sublist]
    if not all_points:
        return None
        
    x_coords = [p[0] for p in all_points]
    y_coords = [p[1] for p in all_points]
    
    # Agregar un pequeño margen
    x_margin = (max(x_coords) - min(x_coords)) * 0.1
    y_margin = (max(y_coords) - min(y_coords)) * 0.1
    
    ax.set_xlim(min(x_coords) - x_margin, max(x_coords) + x_margin)
    ax.set_ylim(min(y_coords) - y_margin, max(y_coords) + y_margin)
    
    # Dibujar cada línea
    for i, points in enumerate(coordinates):
        if len(points) < 2:
            continue
            
        try:
            # Obtener color
            color = colours[i % len(colours)]
            color = tuple(min(1.0, max(0.0, c)) for c in color[:3])  # Asegurar valores entre 0 y 1
            
            # Crear un polígono cerrado
            polygon = patches.Polygon(points, closed=True, 
                                     facecolor=color, 
                                     edgecolor='black',
                                     linewidth=0.5)
            ax.add_patch(polygon)
            
        except Exception as e:
            print(f"Error dibujando polígono: {e}")
            continue
    
    # Guardar la figura en un buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=100)
    plt.close(fig)
    
    # Convertir a base64 para mostrarla en la web
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return img_str

@app.route('/')
def home():
    try:
        img_str = create_flower()
        if img_str is None:
            return "No se pudieron cargar los datos de la flor."
            
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flores para ti</title>
            <style>
                body {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background-color: #f8f9fa;
                    font-family: Arial, sans-serif;
                }}
                .container {{
                    text-align: center;
                    padding: 2rem;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    max-width: 90%;
                }}
                h1 {{
                    color: #e83e8c;
                    margin-bottom: 1.5rem;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 5px;
                    margin: 1rem 0;
                }}
                p {{
                    color: #6c757d;
                    font-size: 1.1rem;
                    margin-top: 1.5rem;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Un detalle para ti ❤️</h1>
                <img src="data:image/png;base64,{img_str}" alt="Flores">
                <p>¡Espero que te guste!</p>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        return f"<h1>Error al generar la imagen: {str(e)}</h1>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
