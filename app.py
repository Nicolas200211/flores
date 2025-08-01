import turtle as tu   
import re   
import docx   
   
source = "tulipanes_actualizado"  
   
data = docx.Document("{}.docx".format(source))   
coordinates = []   
colour = []   
   
for i in data.paragraphs:   
    try :   
        coord_stg_tup = re.findall(r'\([-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)?\)', i.text)   
        coord_num_tup = []   
        color_stg_tup = re.findall(r'\([-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)? ?\, ?[-+]?\d*\.\d*(?:[eE][-+]?\d+)?\)', i.text)   
        color_val = re.findall(r'[-+]?\d*\.\d*',color_stg_tup[0])   
        color_val_lst = [float(k) for k in color_val]   
        colour.append(tuple(color_val_lst))   
   
        for j in coord_stg_tup:   
            coord_pos = re.findall(r'[-+]?\d*\.\d*',j)   
            coord_num_lst = [float(k) for k in coord_pos]   
            coord_num_tup.append(tuple(coord_num_lst))   
   
        coordinates.append(coord_num_tup)   
    except:   
        pass   
 
# Configuración inicial
pen = tu.Turtle()   
screen = tu.Screen()

# Máxima velocidad de dibujo
tu.tracer(10)  # Desactiva la animación
pen.speed(10)   # Velocidad más rápida
pen.hideturtle()

# Configurar pantalla completa
try:
    screen.setup(width=1.0, height=1.0)  # Pantalla completa
    screen.getcanvas().winfo_toplevel().attributes("-fullscreen", True)
except:
    pass  # Si falla, continuar sin pantalla completa

# Función para cerrar la ventana después de 60 segundos
def cerrar_ventana():
    screen.bye()

# Programar el cierre después de 60 segundos (60000 ms)
screen.ontimer(cerrar_ventana, 60000)
   
for i in range(len(coordinates)):   
    draw = 1   
    path = coordinates[i]   
    col = colour[i]   
    pen.color(col)   
    pen.begin_fill()   
    for order_pair in path:   
        x,y = order_pair   
        y = -1*y   
        if draw:   
            pen.up()   
            pen.goto(x,y)   
            pen.down()   
            draw = 0   
        else:   
            pen.goto(x,y)   
    pen.end_fill()   
    # Configurar el texto principal
pen.penup()
pen.goto(0, 250)  # Posición inicial

# Configuración del texto
titulo = '¡FELIZ DÍA DE LA NOVIA!'
fuente = ('Arial', 48, 'bold')

# Configuración de espaciado
tamano_letra = 48  # Tamaño de la fuente
ancho_letra = tamano_letra * 0.5  # Aumentado el ancho de cada letra
espacio_entre_letras = tamano_letra * 0.5  # Espacio generoso entre letras

# Calcular ancho total del texto (aproximado)
ancho_total = len(titulo) * (ancho_letra + espacio_entre_letras)

# Posicionar en el centro
x_inicio = -ancho_total / 2
pen.goto(x_inicio, 250)

# Configurar modo de color de turtle
tu.colormode(255)

# Colores para el degradado (tonos de tulipanes)
colores = [
    (255, 105, 180),  # Rosa fuerte
    (255, 20, 147),   # Rosa profundo
    (219, 112, 147),  # Rosa pálido
    (255, 182, 193),  # Rosa claro
    (199, 21, 133),   # Rosa violeta
    (255, 0, 127),    # Rosa neón
    (255, 0, 0),      # Rojo
    (255, 69, 0),     # Rojo anaranjado
    (186, 85, 211),   # Orquídea
    (147, 112, 219)   # Púrpura medio
]

# Dibujar cada letra
for i, letra in enumerate(titulo):
    pen.color(colores[i % len(colores)])
    pen.write(letra, align='center', font=fuente)
    # Mover el ancho de la letra más el espacio entre letras
    pen.forward(ancho_letra + espacio_entre_letras)

# Dibujar corazón separado
pen.penup()
pen.goto(ancho_total/2 + 30, 250)  # 30 píxeles de separación
pen.color('red')
pen.write('❤️', align='center', font=('Arial', 48, 'bold'))

# Actualizar pantalla
tu.update()

# Mantener la ventana abierta
try:
    screen.mainloop()
except tu.Terminator:
    pass  # Manejar cierre de ventana 