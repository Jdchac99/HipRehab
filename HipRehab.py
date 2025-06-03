import math
import serial
import time

# Configuración del puerto serial para Bluetooth (ajusta el puerto según tu configuración en Windows)
try:
    bt_serial = serial.Serial('COM3', 9600, timeout=0.1)  # Ejemplo: 'COM3' es un puerto común en Windows
except serial.SerialException as e:
    print(f"Error al abrir el puerto Bluetooth: {e}")
    bt_serial = None

# Configuración del puerto serial para la comunicación con Teensy (ajusta el puerto según tu configuración en Windows)
try:
    serial_port = serial.Serial('COM4', 9600, timeout=0.1)  # Ejemplo: 'COM4' es otro puerto común en Windows
except serial.SerialException as e:
    print(f"Error al abrir el puerto serial (Teensy): {e}")
    serial_port = None

pot_pin = 14  # En Arduino, esto se refiere a A0 (pin analógico 0), no directamente traducible

last_angle = -1000.0
max_angle_reached = -1000.0
max_torque_reached = -1000.0
subiendo_angulo = False
repeticiones_completas = 0
repeticiones_incompletas = 0
angulo_meta_app = -1
repeticiones_meta = 0  # Variable para almacenar el número meta de repeticiones
modo_ejercicio = ""  # Variable para almacenar el modo del ejercicio
ejercicio = ""

def comparar_angulos(angulo_potenciometro, angulo_app):
    if angulo_app != -1:
        if angulo_potenciometro >= angulo_app:
            print("Comparación Ángulo: Igual")
        else:
            print("Comparación Ángulo: Diferente")

def setup():
    if bt_serial:
        print("Bluetooth inicializado en {}".format(bt_serial.port))
    else:
        print("Advertencia: No se pudo inicializar el puerto Bluetooth.")
    if serial_port:
        serial_port.reset_input_buffer()
        print("Teensy conectado en {}. Esperando comando...".format(serial_port.port))
    else:
        print("Advertencia: No se pudo inicializar el puerto serial (Teensy).")

def loop():
    global last_angle, max_angle_reached, max_torque_reached, subiendo_angulo
    global repeticiones_completas, repeticiones_incompletas, angulo_meta_app
    global repeticiones_meta, modo_ejercicio, ejercicio

    last_send = time.time()
    pot_value = 0
    # Emular la lectura analógica del potenciómetro leyendo desde el puerto serial
    if serial_port and serial_port.in_waiting > 0:
        try:
            line = serial_port.readline().decode('utf-8').rstrip()
            if line.startswith("valorPot:"):
                try:
                    pot_value = int(line.split(":")[1])
                except ValueError:
                    print(f"Error al convertir el valor del potenciómetro: {line}")
        except serial.SerialException as e:
            print(f"Error de lectura del puerto serial (Teensy): {e}")
        except UnicodeDecodeError as e:
            print(f"Error de decodificación del puerto serial (Teensy): {e}")

    # Emular el envío por Bluetooth
    if bt_serial:
        try:
            bt_serial.write(f"valorPot:{pot_value}\n".encode('utf-8'))
        except serial.SerialException as e:
            print(f"Error al escribir en el puerto Bluetooth: {e}")

    current_angle_base = 0.0
    val = 0

    # Aplicar ajuste de ángulo basado en el modo
    if modo_ejercicio == "Sentado":
        current_angle_base = -0.3008 * pot_value + 205.7
        val = 67
    else:
        current_angle_base = -0.2866 * potValue + 140.56
        val = 12

    current_angle = current_angle_base
    limit = val

    current_angle_radians = math.radians(current_angle)
    current_torque = 0.0  # Declarar current_torque fuera de los if
    if ejercicio == "Extensión":
        current_torque = 6.24 * math.cos(current_angle_radians) + 51.0 * current_angle_radians
    else:
        current_torque = 6.24 * math.cos(current_angle_radians) + 37.0 * current_angle_radians

    if abs(current_angle) < limit and not subiendo_angulo:
        subiendo_angulo = True
        max_angle_reached = current_angle

    if subiendo_angulo:
        if current_angle > max_angle_reached:
            max_angle_reached = current_angle
        if current_angle < max_angle_reached and (max_angle_reached > limit or max_angle_reached < -limit):
            if abs(current_angle) < limit:
                print(f"Máximo Ángulo Alcanzado: {max_angle_reached}")
                if bt_serial:
                    try:
                        bt_serial.write(f"AnguloMaximo:{max_angle_reached}\n".encode('utf-8'))
                    except serial.SerialException as e:
                        print(f"Error al escribir en el puerto Bluetooth: {e}")
                comparar_angulos(max_angle_reached, angulo_meta_app)
                if ejercicio == "Extensión":
                    max_angle_radians = math.radians(max_angle_reached)
                    max_torque_reached = 51.0 * max_angle_radians
                    if bt_serial:
                        try:
                            bt_serial.write(f"TorqueMaximo:{max_torque_reached}\n".encode('utf-8'))
                        except serial.SerialException as e:
                            print(f"Error al escribir en el puerto Bluetooth: {e}")
                else:
                    max_angle_radians = math.radians(max_angle_reached)
                    max_torque_reached = 37.0 * max_angle_radians
                    if bt_serial:
                        try:
                            bt_serial.write(f"TorqueMaximo:{max_torque_reached}\n".encode('utf-8'))
                        except serial.SerialException as e:
                            print(f"Error al escribir en el puerto Bluetooth: {e}")

                if angulo_meta_app != -1 and max_angle_reached >= angulo_meta_app:
                    repeticiones_completas += 1
                    print(f"Repetición Completa: {repeticiones_completas}")
                    print(f"Repeticiones Meta: {repeticiones_meta}")
                    if bt_serial:
                        try:
                            bt_serial.write(f"RepeticionesCompletas:{repeticiones_completas}\n".encode('utf-8'))
                        except serial.SerialException as e:
                            print(f"Error al escribir en el puerto Bluetooth: {e}")
                elif (max_angle_reached > limit or max_angle_reached < limit) and angulo_meta_app != -1 and max_angle_reached < angulo_meta_app:
                    repeticiones_incompletas += 1
                    print(f"Repetición Incompleta: {repeticiones_incompletas}")
                    if bt_serial:
                        try:
                            bt_serial.write(f"RepeticionesIncompletas:{repeticiones_incompletas}\n".encode('utf-8'))
                        except serial.SerialException as e:
                            print(f"Error al escribir en el puerto Bluetooth: {e}")
                elif (max_angle_reached > limit or max_angle_reached < -limit) and angulo_meta_app == -1:
                    repeticiones_completas += 1
                    print(f"Repetición Completa (sin meta): {repeticiones_completas}")
                    if bt_serial:
                        try:
                            bt_serial.write(f"RepeticionesCompletas:{repeticiones_completas}\n".encode('utf-8'))
                        except serial.SerialException as e:
                            print(f"Error al escribir en el puerto Bluetooth: {e}")
                subiendo_angulo = False
                max_angle_reached = -1000.0

    if abs(current_angle - last_angle) > 0.5 or last_angle == -1000.0:
        print(f"Angulo: {current_angle} Torque: {current_torque} Tension:{pot_value} Completas: {repeticiones_completas} Incompletas: {repeticiones_incompletas}")
        last_angle = current_angle

    if bt_serial and bt_serial.in_waiting > 0:
        time.sleep(0.01)
        try:
            command = bt_serial.readline().decode('utf-8').rstrip()
            print(f"Dato Recibido App: {command}")

            if command.startswith("Flexión"):
                print("¡Ejercicio seleccionado: Flexión!")
                ejercicio = "Flexión"
            elif command.startswith("Extensión"):
                print("¡Ejercicio seleccionado: Extensión!")
                ejercicio = "Extensión"
            elif command.startswith("Ejercicio:"):
                parts = command.split(',')
                ejercicio_part = next((p for p in parts if p.startswith("Ejercicio:")), None)
                pierna_part = next((p for p in parts if p.startswith("Pierna:")), None)
                modo_part = next((p for p in parts if p.startswith("Modo:")), None)
                series_part = next((p for p in parts if p.startswith("Series:")), None)
                repeticiones_part = next((p for p in parts if p.startswith("Repeticiones:")), None)
                angulo_meta_part = next((p for p in parts if p.startswith("AnguloMeta:")), None)

                if ejercicio_part and pierna_part and modo_part and series_part and repeticiones_part and angulo_meta_part:
                    ejercicio = ejercicio_part.split(':')[1]
                    pierna = pierna_part.split(':')[1]
                    modo_ejercicio = modo_part.split(':')[1]
                    series_meta = series_part.split(':')[1]
                    repeticiones_meta_str = repeticiones_part.split(':')[1]
                    angulo_meta_app_str = angulo_meta_part.split(':')[1]

                    try:
                        repeticiones_meta = int(repeticiones_meta_str)
                        angulo_meta_app = int(angulo_meta_app_str)
                    except ValueError:
                        print("Error al convertir repeticiones o ángulo meta.")
                        angulo_meta_app = -1
                        repeticiones_meta = 0
                        modo_ejercicio = ""

                    print(f"Ejercicio: {ejercicio}")
                    print(f"Pierna: {pierna}")
                    print(f"Modo: {modo_ejercicio}")
                    print(f"Series: {series_meta}")
                    print(f"Repeticiones Meta (recibido): {repeticiones_meta}")
                    print(f"Ángulo Meta App (recibido): {angulo_meta_app}")
                    repeticiones_completas = 0
                    repeticiones_incompletas = 0
                else:
                    print("Formato de comando no reconocido.")
                    angulo_meta_app = -1
                    repeticiones_meta = 0
                    modo_ejercicio = ""
            elif len(command) > 0:
                print(f"Comando recibido: {command}")
        except serial.SerialException as e:
            print(f"Error al leer del puerto Bluetooth: {e}")
        except UnicodeDecodeError as e:
            print(f"Error de decodificación Bluetooth: {e}")

    time.sleep(0.1)

if __name__ == "__main__":
    setup()
    while True:
        loop()


     
           
         
            
  
