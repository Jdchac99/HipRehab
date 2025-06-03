#define BT Serial1
#include <math.h>

const int potPin = 14;

float lastAngle = -1000.0;
float maxAngleReached = -1000.0;
float maxtorqueReached = -1000.0;
bool subiendoAngulo = false;
int repeticionesCompletas = 0;
int repeticionesIncompletas = 0;
int anguloMetaApp = -1;
int repeticionesMeta = 0; // Variable para almacenar el número meta de repeticiones
String modoEjercicio = ""; // Variable para almacenar el modo del ejercicio
String ejercicio = "";

void compararAngulos(float anguloPotenciometro, int anguloApp) {
  if (anguloApp != -1) {
    if (anguloPotenciometro >= anguloApp) {
      Serial.println("Comparación Ángulo: Igual");
    } else {
      Serial.println("Comparación Ángulo: Diferente");
    }
  }
}

void setup() {
  BT.begin(9600);
  Serial.begin(9600);
  Serial.println("Teensy conectado. Esperando comando...");
}

void loop() {
  static unsigned long lastSend = 0;
  int potValue = analogRead(potPin);
  // Enviar el valor por Bluetooth con el formato "valorPot:[valor]"
  BT.print("valorPot:");  // Prefijo identificador
  BT.println(potValue);   // Valor + salto de línea
  //float currentAngleBase = -0.2866 * potValue + 144.56;
  //float currentAngle = currentAngleBase; // Inicializamos con la ecuación base
  float currentAngleBase;
  int val;

  // Aplicar ajuste de ángulo basado en el modo
  if (modoEjercicio == "Sentado") {
    currentAngleBase = -0.3008 * potValue + 205.7;
    val = 67;
  }
  else{
    currentAngleBase = -0.2866 * potValue + 140.56;
    val = 12;
  }
  float currentAngle = currentAngleBase; 
  int limit = val;
  

  float currentAngleRadians = currentAngle * PI / 180.0;
  float currentTorque = 0.0; // Declarar currentTorque fuera de los if
  if (ejercicio == "Extensión") {
    currentTorque = 6.24*cos(currentAngleRadians)+51.0 * currentAngleRadians;
  }
  else {
    currentTorque = 6.24*cos(currentAngleRadians)+37.0 * currentAngleRadians;

  }
  

  if (abs(currentAngle) < limit && !subiendoAngulo) {
    subiendoAngulo = true;
    maxAngleReached = currentAngle;
  }

  if (subiendoAngulo) {
    if (currentAngle > maxAngleReached) {
      maxAngleReached = currentAngle;
    }
    if (currentAngle < maxAngleReached && (maxAngleReached > limit || maxAngleReached < -limit)) {
      if (abs(currentAngle) < limit) {
        Serial.print("Máximo Ángulo Alcanzado: ");
        Serial.println(maxAngleReached);
        BT.print("AnguloMaximo:");
        BT.println(maxAngleReached);
        compararAngulos(maxAngleReached, anguloMetaApp);
        if (ejercicio == "Extensión") {
          float maxAngleRadians = maxAngleReached * PI / 180.0;
          maxtorqueReached = 51.0 * maxAngleRadians;
          BT.print("TorqueMaximo:");
          BT.println(maxtorqueReached);
          }
        else {
          float maxAngleRadians = maxAngleReached * PI / 180.0;
          maxtorqueReached = 37.0 * maxAngleRadians;
          BT.print("TorqueMaximo:");
          BT.println(maxtorqueReached);
        }
  

        if (anguloMetaApp != -1 && maxAngleReached >= anguloMetaApp) {
          repeticionesCompletas++;
          Serial.print("Repetición Completa: ");
          Serial.println(repeticionesCompletas);
          Serial.print("Repeticiones Meta: ");
          Serial.println(repeticionesMeta);
          // Enviar el número de repeticiones completas al Android
          BT.print("RepeticionesCompletas:");
          BT.println(repeticionesCompletas);
          //if (repeticionesCompletas >= repeticionesMeta && repeticionesMeta != 0) { // Verifica si se alcanza la meta
          //Serial.println("¡Meta de repeticiones alcanzada! Reiniciando contador.");

          //repeticionesCompletas = 0; // Reinicia el contador
          //}
        } else if ((maxAngleReached > limit || maxAngleReached < limit) && anguloMetaApp != -1 && maxAngleReached < anguloMetaApp) {
          repeticionesIncompletas++;
          Serial.print("Repetición Incompleta: ");
          Serial.println(repeticionesIncompletas);
          BT.print("RepeticionesIncompletas:");
          BT.println(repeticionesIncompletas);
        } else if ((maxAngleReached > limit || maxAngleReached < -limit) && anguloMetaApp == -1) {
          repeticionesCompletas++;
          Serial.print("Repetición Completa (sin meta): ");
          Serial.println(repeticionesCompletas);
          // Enviar el número de repeticiones completas al Android
          BT.print("RepeticionesCompletas:");
          BT.println(repeticionesCompletas);
        }
        subiendoAngulo = false;
        maxAngleReached = -1000.0;
      }
    }
  }

  if (abs(currentAngle - lastAngle) > 0.5 || lastAngle == -1000.0) {
    Serial.print("Angulo: ");
    Serial.print(currentAngle);
    Serial.print(" Torque: ");
    Serial.print(currentTorque);
    Serial.print("Tension:");
    Serial.print(potValue);
    Serial.print(" Completas: ");
    Serial.print(repeticionesCompletas);
    Serial.print(" Incompletas: ");
    Serial.println(repeticionesIncompletas);
    lastAngle = currentAngle;
  }

  if (BT.available()) {
    delay(10);
    String command = BT.readStringUntil('\n');
    command.trim();
    Serial.print("Dato Recibido App: ");
    Serial.println(command);

    if (command.startsWith("Flexión")) {
      Serial.println("¡Ejercicio seleccionado: Flexión!");
      ejercicio = "Flexión";
    } else if (command.startsWith("Extensión")) {
      Serial.println("¡Ejercicio seleccionado: Extensión!");
      ejercicio = "Extensión";
    } else if (command.startsWith("Ejercicio:")) {
      int ejercicioIndex = command.indexOf(':');
      int piernaIndex = command.indexOf(",Pierna:");
      int modoIndex = command.indexOf(",Modo:"); // Encontrar el índice de "Modo:"
      int seriesIndex = command.indexOf(",Series:");
      int repeticionesIndex = command.indexOf(",Repeticiones:");
      int anguloMetaIndex = command.indexOf(",AnguloMeta:");

      if (ejercicioIndex != -1 && piernaIndex != -1 && modoIndex != -1 && seriesIndex != -1 && repeticionesIndex != -1 && anguloMetaIndex != -1) {
        ejercicio = command.substring(ejercicioIndex + 1, piernaIndex);
        String pierna = command.substring(piernaIndex + 8, modoIndex); // Extraer la pierna antes del modo
        modoEjercicio = command.substring(modoIndex + 6, seriesIndex); // Extraer el modo
        String seriesMeta = command.substring(seriesIndex + 8, repeticionesIndex);
        String repeticionesMetaStr = command.substring(repeticionesIndex + 13, anguloMetaIndex);
        anguloMetaApp = command.substring(anguloMetaIndex + 12).toInt();
        // Eliminar el ":" si está presente
        if (repeticionesMetaStr.startsWith(":")) {
          repeticionesMetaStr = repeticionesMetaStr.substring(1);
        }
        repeticionesMeta = repeticionesMetaStr.toInt(); // Convierte el string a int y lo asigna a repeticionesMeta
        Serial.print("Ejercicio: ");
        Serial.println(ejercicio);
        Serial.print("Pierna: ");
        Serial.println(pierna);
        Serial.print("Modo: ");
        Serial.println(modoEjercicio);
        Serial.print("Series: ");
        Serial.println(seriesMeta);
        Serial.print("Repeticiones (string): ");
        Serial.println(repeticionesMetaStr);
        Serial.print("Repeticiones Meta (recibido): ");
        Serial.println(repeticionesMeta);
        Serial.print("Ángulo Meta App (recibido): ");
        Serial.println(anguloMetaApp);
        repeticionesCompletas = 0;
        repeticionesIncompletas = 0;
      } else {
        Serial.println("Formato de comando no reconocido.");
        anguloMetaApp = -1;
        repeticionesMeta = 0;
        modoEjercicio = ""; // Reiniciar el modo en caso de error
      }
    } else if (command.length() > 0) {
      Serial.print("Comando recibido: ");
      Serial.println(command);
    }
  }

  delay(100);
}
