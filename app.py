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
    try:
        # Leer el documento con las coordenadas
        source = "tulipanes_actualizado"
        data = docx.Document(f"{source}.docx")
        coordinates = []
        colours = []

        for i in data.paragraphs:
            try:
                # Extraer coordenadas (usando la misma expresión regular que en tulipanes.py)
                coord_stg_tup = re.findall(
                    r'\([-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)?\)', 
                    i.text
                )
                coord_num_tup = []
                
                # Extraer colores (usando la misma expresión regular que en tulipanes.py)
                color_stg_tup = re.findall(
                    r'\([-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)?\)', 
                    i.text
                )
                
                if not color_stg_tup:
                    continue
                    
                color_val = re.findall(r'[-+]?\d*\.\d*', color_stg_tup[0])
                color_val_lst = [float(k) for k in color_val]
                colours.append(tuple(color_val_lst))
                
                # Procesar coordenadas
                for j in coord_stg_tup:
                    coord_pos = re.findall(r'[-+]?\d*\.\d*', j)
                    coord_num_lst = [float(k) for k in coord_pos]
                    coord_num_tup.append(tuple(coord_num_lst))
                
                coordinates.append(coord_num_tup)
                
            except Exception as e:
                print(f"Error procesando párrafo: {e}")
                continue
        
        return coordinates, colours
        
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None, None

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
@app.route('/', methods=['GET', 'POST'])
def home():
    try:
        # Obtener las coordenadas y colores
        coordinates, colours = create_flower()
        
        if not coordinates or not colours:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px; 
                        background-color: #fff0f0;
                    }
                    .error { 
                        color: #d32f2f; 
                        background: #ffebee; 
                        padding: 20px; 
                        border-radius: 5px; 
                        max-width: 600px; 
                        margin: 0 auto;
                        border: 1px solid #ef9a9a;
                    }
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>¡Ups! Algo salió mal</h1>
                    <p>No se pudieron cargar los datos de la flor. Por favor, verifica que el archivo 'tulipanes_actualizado.docx' esté en el directorio correcto.</p>
                    <p>Si el problema persiste, por favor contacta al administrador.</p>
                </div>
            </body>
            </html>
            """
        
        # Crear la figura de Matplotlib
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Dibujar cada forma
        for coords, color in zip(coordinates, colours):
            if not coords:
                continue
            x_vals = [x for x, y in coords]
            y_vals = [y for x, y in coords]
            ax.fill(x_vals, y_vals, color=[c/255 for c in color])
        
        # Guardar la imagen en un buffer
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
        plt.close(fig)
        img.seek(0)
        
        # Convertir a base64
        img_str = base64.b64encode(img.getvalue()).decode('utf-8')
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flores para Ti</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                    background-color: #f0f8ff;
                    font-family: 'Arial', sans-serif;
                }}
                .container {{
                    text-align: center;
                    max-width: 800px;
                    width: 100%;
                }}
                h1 {{
                    color: #ff69b4;
                    margin-bottom: 20px;
                    font-size: 2.5em;
                }}
                .flower-container {{
                    background: white;
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    margin: 20px 0;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 10px;
                }}
                .message {{
                    margin-top: 25px;
                    font-size: 1.3em;
                    color: #333;
                    line-height: 1.6;
                }}
                .signature {{
                    margin-top: 15px;
                    font-style: italic;
                    color: #666;
                }}
                @media (max-width: 600px) {{
                    h1 {{
                        font-size: 2em;
                    }}
                    .message {{
                        font-size: 1.1em;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>¡Flores para ti! 💐</h1>
                <div class="flower-container">
                    <img src="data:image/png;base64,{img_str}" alt="Flor generada">
                </div>
                <div class="message">
                    <p>Con todo mi cariño,</p>
                    <div class="signature">
                        <p>💖</p>
                        <p>Para la persona más especial</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        import traceback
        error_msg = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px; 
                    background-color: #fff0f0;
                }}
                .error {{ 
                    color: #d32f2f; 
                    background: #ffebee; 
                    padding: 20px; 
                    border-radius: 5px; 
                    max-width: 800px; 
                    margin: 0 auto;
                    border: 1px solid #ef9a9a;
                    text-align: left;
                    white-space: pre-wrap;
                    font-family: monospace;
                }}
                h1 {{ color: #b71c1c; }}
            </style>
        </head>
        <body>
            <h1>¡Error al generar la imagen!</h1>
            <div class="error">
                {str(e)}
                
                Traceback:
                {traceback.format_exc()}
            </div>
        </body>
        </html>
        """
        return error_msg

@app.route('/health')
def health_check():
    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
