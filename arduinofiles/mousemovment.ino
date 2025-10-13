#include <Mouse.h>

void setup() {
  Serial.begin(9600);
  Mouse.begin();
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');

    if (input.startsWith("move")) {
      int separatorIndex = input.indexOf(',');
      if (separatorIndex > 0) {
        int x = input.substring(5, separatorIndex).toInt();
        int y = input.substring(separatorIndex + 1).toInt();

        Mouse.move(x, y);
      }
    } else if (input == "down") {
      Mouse.press(MOUSE_LEFT);
    } else if (input == "up") {
      Mouse.release(MOUSE_LEFT);
    }
  }
}
