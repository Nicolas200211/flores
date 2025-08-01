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
    """
    Lee el archivo de Word con las coordenadas y colores de la flor.
    Devuelve una tupla (coordinates, colours) o (None, None) en caso de error.
    """
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
                
                # Solo agregar el color si hay coordenadas válidas
                if coord_stg_tup:
                    # Asegurarse de que los valores de color estén entre 0 y 1
                    normalized_color = []
                    for c in color_val_lst[:3]:  # Solo tomamos los primeros 3 valores (RGB)
                        c_float = float(c)
                        if c_float > 1.0 and c_float <= 255.0:  # Si está en rango 0-255, normalizar
                            c_float = c_float / 255.0
                        normalized_color.append(max(0.0, min(1.0, c_float)))  # Asegurar entre 0 y 1
                    
                    # Asegurarse de que tenemos 3 componentes de color
                    while len(normalized_color) < 3:
                        normalized_color.append(0.0)  # Rellenar con negro si faltan componentes
                    
                    colours.append(tuple(normalized_color[:3]))  # Tomar solo RGB (ignorar alpha si existe)
                    
                    # Procesar coordenadas
                    for j in coord_stg_tup:
                        coord_pos = re.findall(r'[-+]?\d*\.\d*', j)
                        if len(coord_pos) >= 2:  # Asegurarse de que hay al menos x e y
                            try:
                                x = float(coord_pos[0])
                                y = float(coord_pos[1])
                                coord_num_tup.append((x, y))
                            except (ValueError, IndexError) as e:
                                print(f"Error convirtiendo coordenadas: {e}")
                                continue
                    
                    if coord_num_tup:  # Solo agregar si hay coordenadas válidas
                        coordinates.append(coord_num_tup)
                
            except Exception as e:
                print(f"Error procesando párrafo: {e}")
                continue
        
        # Verificar que tenemos datos válidos
        if not coordinates or not colours:
            print("No se encontraron coordenadas o colores válidos")
            return None, None
            
        return coordinates, colours
        
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None, None
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
        
        # Encontrar límites para escalar correctamente
        all_points = [point for sublist in coordinates for point in sublist if sublist]
        if all_points:  # Solo si hay puntos válidos
            x_coords = [p[0] for p in all_points]
            y_coords = [p[1] for p in all_points]
            
            # Calcular el centro y el tamaño
            x_center = (min(x_coords) + max(x_coords)) / 2
            y_center = (min(y_coords) + max(y_coords)) / 2
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            
            # Usar el máximo entre ancho y alto para hacerlo cuadrado
            size = max(width, height) * 1.2  # 20% de margen
            
            # Establecer límites centrados
            ax.set_xlim(x_center - size/2, x_center + size/2)
            # Invertir el eje Y para que coincida con el sistema de Turtle
            ax.set_ylim(y_center + size/2, y_center - size/2)
        
        # Dibujar cada forma
        for i, coords in enumerate(coordinates):
            if not coords or len(coords) < 2:
                continue
                
            try:
                # Obtener el color correspondiente (usar módulo para evitar índices fuera de rango)
                color = colours[i % len(colours)]
                
                # Crear un polígono cerrado
                # Asegurarse de que hay al menos 3 puntos para un polígono
                if len(coords) >= 3:
                    polygon = patches.Polygon(
                        coords,
                        closed=True,
                        facecolor=color,
                        edgecolor='none',
                        linewidth=0.5,
                        joinstyle='round'
                    )
                    ax.add_patch(polygon)
                # Si solo hay 2 puntos, dibujar una línea
                elif len(coords) == 2:
                    line = patches.Polygon(
                        coords,
                        closed=False,
                        color=color,
                        linewidth=1.0
                    )
                    ax.add_patch(line)
                
            except Exception as e:
                print(f"Error dibujando polígono: {e}")
                continue
        
        # Guardar la imagen en un buffer
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', pad_inches=0.1, dpi=100)
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
                    max-height: 70vh;
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
