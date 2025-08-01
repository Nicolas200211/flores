from flask import Flask, render_template_string, jsonify
import re
import docx
import json
import math
import time

app = Flask(__name__)

def get_drawing_data():
    """
    Lee el archivo de Word con las coordenadas y colores de la flor.
    Devuelve los datos necesarios para la animación.
    """
    try:
        # Leer el documento con las coordenadas
        source = "tulipanes_actualizado"
        data = docx.Document(f"{source}.docx")
        drawing_steps = []
        
        for i in data.paragraphs:
            try:
                # Extraer coordenadas
                coord_stg_tup = re.findall(
                    r'\([-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)?\)', 
                    i.text
                )
                
                # Extraer colores
                color_stg_tup = re.findall(
                    r'\([-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)?\)', 
                    i.text
                )
                
                if not color_stg_tup or not coord_stg_tup:
                    continue
                
                # Procesar color
                color_val = re.findall(r'[-+]?\d*\.\d*', color_stg_tup[0])
                color_val_lst = [float(k) for k in color_val]
                
                # Normalizar color a formato RGB (0-255)
                color_rgb = []
                for c in color_val_lst[:3]:  # Tomar solo RGB
                    c_float = float(c)
                    if c_float <= 1.0:  # Si ya está normalizado (0-1)
                        c_float = c_float * 255
                    color_rgb.append(min(255, max(0, int(c_float))))
                
                # Asegurar que tenemos 3 componentes
                while len(color_rgb) < 3:
                    color_rgb.append(0)
                
                color_hex = '#%02x%02x%02x' % tuple(color_rgb[:3])
                
                # Procesar coordenadas
                points = []
                for j in coord_stg_tup:
                    coord_pos = re.findall(r'[-+]?\d*\.\d*', j)
                    if len(coord_pos) >= 2:
                        try:
                            x = float(coord_pos[0])
                            y = float(coord_pos[1])
                            points.append({'x': x, 'y': y})
                        except (ValueError, IndexError) as e:
                            print(f"Error procesando coordenadas: {e}")
                            continue
                
                if points:  # Solo agregar si hay puntos válidos
                    drawing_steps.append({
                        'color': color_hex,
                        'points': points,
                        'is_polygon': len(points) > 2  # Si tiene 3 o más puntos, es un polígono
                    })
                
            except Exception as e:
                print(f"Error procesando párrafo: {e}")
                continue
        
        return drawing_steps if drawing_steps else None
        
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
@app.route('/')
def home():
    try:
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Flores para Ti - Animación</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background-color: #f0f8ff;
            font-family: 'Arial', sans-serif;
            overflow: hidden;
        }
        .container {
            text-align: center;
            width: 100%;
            max-width: 800px;
            padding: 20px;
            box-sizing: border-box;
        }
        h1 {
            color: #ff69b4;
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        .canvas-container {
                background: white;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin: 0 auto;
                overflow: hidden;
                position: relative;
            }
            canvas {
                display: block;
                max-width: 100%;
                height: auto;
                margin: 0 auto;
            }
            .controls {
                margin: 20px 0;
                display: flex;
                justify-content: center;
                gap: 10px;
            }
            button {
                background-color: #ff69b4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #ff4d9e;
            }
            button:disabled {
                background-color: #cccccc;
                cursor: not-allowed;
            }
            .message {
                margin-top: 25px;
                font-size: 1.3em;
                color: #333;
                line-height: 1.6;
            }
            .signature {
                margin-top: 15px;
                font-style: italic;
                color: #666;
            }
            @media (max-width: 600px) {
                h1 {
                    font-size: 2em;
                }
                .message {
                    font-size: 1.1em;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>¡Flores para ti! 💐</h1>
            <div class="canvas-container">
                <canvas id="flowerCanvas"></canvas>
            </div>
            <div class="controls">
                <button id="startBtn">Comenzar animación</button>
                <button id="resetBtn">Reiniciar</button>
            </div>
            <div class="message">
                <p>Con todo mi cariño,</p>
                <div class="signature">
                    <p>💖</p>
                    <p>Para la persona más especial</p>
                </div>
            </div>
        </div>

        <script>
            // Variables globales
            let drawingData = [];
            let currentStep = 0;
            let isDrawing = false;
            let animationId = null;
            let canvas, ctx;
            let scale = 1;
            let offsetX = 0;
            let offsetY = 0;

            // Inicializar el canvas
            function initCanvas() {
                canvas = document.getElementById('flowerCanvas');
                // Ajustar tamaño del canvas
                const container = canvas.parentElement;
                const size = Math.min(container.clientWidth, window.innerHeight * 0.6, 800);
                canvas.width = size;
                canvas.height = size;
                
                // Obtener contexto 2D
                ctx = canvas.getContext('2d');
                
                // Escalar y centrar el dibujo
                scaleCanvas();
                
                // Cargar los datos del dibujo
                loadDrawingData();
            }
            
            // Escalar el canvas para que quepa el dibujo completo
            function scaleCanvas() {
                if (!drawingData.length) return;
                
                // Encontrar límites del dibujo
                let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                
                drawingData.forEach(step => {
                    step.points.forEach(point => {
                        minX = Math.min(minX, point.x);
                        minY = Math.min(minY, point.y);
                        maxX = Math.max(maxX, point.x);
                        maxY = Math.max(maxY, point.y);
                    });
                });
                
                // Calcular dimensiones
                const width = maxX - minX;
                const height = maxY - minY;
                const centerX = (minX + maxX) / 2;
                const centerY = (minY + maxY) / 2;
                
                // Calcular escala para que quepa en el canvas con un margen
                const margin = 1.2; // 20% de margen
                scale = Math.min(
                    (canvas.width / width) * 0.9 * margin,
                    (canvas.height / height) * 0.9 * margin
                ) || 1; // Evitar división por cero
                
                // Calcular desplazamiento para centrar
                offsetX = (canvas.width / 2) - (centerX * scale);
                offsetY = (canvas.height / 2) - (centerY * scale);
            }
            
            // Cargar los datos del dibujo desde el servidor
            async function loadDrawingData() {
                try {
                    const response = await fetch('/drawing-data');
                    if (!response.ok) throw new Error('Error al cargar los datos del dibujo');
                    drawingData = await response.json();
                    scaleCanvas();
                    updateControls();
                } catch (error) {
                    console.error('Error:', error);
                    alert('No se pudieron cargar los datos del dibujo. Por favor, recarga la página.');
                }
            }
            
            // Convertir coordenadas del mundo al canvas
            function toCanvasCoords(x, y) {
                return {
                    x: (x * scale) + offsetX,
                    y: (y * scale) + offsetY
                };
            }
            
            // Dibujar un paso de la animación
            function drawStep(stepIndex) {
                if (stepIndex < 0 || stepIndex >= drawingData.length) return;
                
                const step = drawingData[stepIndex];
                const points = step.points;
                
                if (points.length < 2) return;
                
                // Configurar el estilo
                ctx.strokeStyle = step.color;
                ctx.fillStyle = step.is_polygon ? step.color : 'transparent';
                ctx.lineWidth = 2;
                ctx.lineJoin = 'round';
                ctx.lineCap = 'round';
                
                // Comenzar un nuevo trazado
                ctx.beginPath();
                
                // Mover al primer punto
                const firstPoint = toCanvasCoords(points[0].x, points[0].y);
                ctx.moveTo(firstPoint.x, firstPoint.y);
                
                // Dibujar líneas a los siguientes puntos
                for (let i = 1; i < points.length; i++) {
                    const point = toCanvasCoords(points[i].x, points[i].y);
                    ctx.lineTo(point.x, point.y);
                }
                
                // Cerrar el trazado si es un polígono
                if (step.is_polygon && points.length > 2) {
                    ctx.closePath();
                    ctx.fill(); // Rellenar el polígono
                }
                
                // Dibujar el borde
                ctx.stroke();
            }
            
            // Animar el dibujo paso a paso
            function animateDrawing() {
                if (currentStep >= drawingData.length) {
                    stopDrawing();
                    return;
                }
                
                // Dibujar el paso actual
                drawStep(currentStep);
                currentStep++;
                
                // Continuar con el siguiente paso
                animationId = requestAnimationFrame(animateDrawing);
            }
            
            // Detener la animación
            function stopDrawing() {
                if (animationId) {
                    cancelAnimationFrame(animationId);
                    animationId = null;
                }
                isDrawing = false;
                updateControls();
            }
            
            // Reiniciar el dibujo
            function resetDrawing() {
                stopDrawing();
                currentStep = 0;
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                updateControls();
            }
            
            // Actualizar el estado de los controles
            function updateControls() {
                const startBtn = document.getElementById('startBtn');
                const resetBtn = document.getElementById('resetBtn');
                
                if (isDrawing) {
                    startBtn.textContent = 'Pausar';
                    startBtn.disabled = false;
                } else if (currentStep >= drawingData.length) {
                    startBtn.textContent = 'Animación completada';
                    startBtn.disabled = true;
                } else if (currentStep > 0) {
                    startBtn.textContent = 'Continuar';
                    startBtn.disabled = false;
                } else {
                    startBtn.textContent = 'Comenzar animación';
                    startBtn.disabled = false;
                }
                
                resetBtn.disabled = currentStep === 0 && !isDrawing;
            }
            
            // Manejadores de eventos
            document.getElementById('startBtn').addEventListener('click', () => {
                if (isDrawing) {
                    stopDrawing();
                } else {
                    isDrawing = true;
                    updateControls();
                    animateDrawing();
                }
            });
            
            document.getElementById('resetBtn').addEventListener('click', resetDrawing);
            
            // Redimensionar el canvas cuando cambia el tamaño de la ventana
            window.addEventListener('resize', () => {
                const container = canvas.parentElement;
                const size = Math.min(container.clientWidth, window.innerHeight * 0.6, 800);
                
                // Solo redimensionar si el tamaño cambia significativamente
                if (Math.abs(canvas.width - size) > 10) {
                    // Guardar el progreso actual
                    const progress = currentStep / drawingData.length;
                    
                    // Redimensionar
                    canvas.width = size;
                    canvas.height = size;
                    
                    // Recalcular la escala y el desplazamiento
                    scaleCanvas();
                    
                    // Redibujar todo hasta el paso actual
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    for (let i = 0; i < currentStep; i++) {
                        drawStep(i);
                    }
                }
                
                // Actualizar el estado de los controles
                function updateControls() {
                    const startBtn = document.getElementById('startBtn');
                    const resetBtn = document.getElementById('resetBtn');
                    
                    if (isDrawing) {
                        startBtn.textContent = 'Pausar';
                        startBtn.disabled = false;
                    } else if (currentStep >= drawingData.length) {
                        startBtn.textContent = 'Animación completada';
                        startBtn.disabled = true;
                    } else if (currentStep > 0) {
                        startBtn.textContent = 'Continuar';
                        startBtn.disabled = false;
                    } else {
                        startBtn.textContent = 'Comenzar animación';
                        startBtn.disabled = false;
                    }
                document.getElementById('startBtn').addEventListener('click', () => {
                    if (isDrawing) {
                        stopDrawing();
                    } else {
                        isDrawing = true;
                        updateControls();
                        animateDrawing();
                    }
                });
                
                document.getElementById('resetBtn').addEventListener('click', resetDrawing);
                
                // Redimensionar el canvas cuando cambia el tamaño de la ventana
                window.addEventListener('resize', () => {
                    if (!canvas) return;
                    const container = canvas.parentElement;
                    const size = Math.min(container.clientWidth, window.innerHeight * 0.6, 800);
                    
                    // Solo redimensionar si el tamaño cambia significativamente
                    if (Math.abs(canvas.width - size) > 10) {
                        // Redimensionar
                        canvas.width = size;
                        canvas.height = size;
                        
                        // Recalcular la escala y el desplazamiento
                        scaleCanvas();
                        
                        // Redibujar todo hasta el paso actual
                        if (ctx) {  // Verificar que el contexto existe
                            ctx.clearRect(0, 0, canvas.width, canvas.height);
                            for (let i = 0; i < currentStep; i++) {
                                drawStep(i);
                            }
                        }
                    }
                });
            }
            
            // Inicializar cuando el DOM esté listo
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    initCanvas();
                    setupEventListeners();
                });
            } else {
                // Si el DOM ya está cargado, inicializar directamente
                initCanvas();
                setupEventListeners();
            }
            }
            </script>
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

@app.route('/drawing-data')
def get_drawing_data():
    """Endpoint para obtener los datos del dibujo en formato JSON"""
    drawing_data = get_drawing_data()
    if drawing_data is None:
        return jsonify({"error": "No se pudo cargar el dibujo"}), 500
    return jsonify(drawing_data)

@app.route('/health')
def health_check():
    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
