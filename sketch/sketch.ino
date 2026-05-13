/*
 * Monkey Island Insult Sword Fight - MCU Sketch
 * ===============================================
 * Receives game events via Bridge from the Linux/Python side
 * and responds with LED matrix animations on the Arduino UNO Q.
 *
 * Events:
 *   "START"   -> Sword clash animation
 *   "CORRECT" -> Green flash / triumphant pattern
 *   "WRONG"   -> Red flash / defeated pattern
 *   "WIN"     -> Victory celebration animation
 *   "LOSE"    -> Defeat animation
 */

#include <Arduino_RouterBridge.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;

// Animation frames as 12x8 bit arrays (stored as uint32_t[3] per frame)

// Sword crossed pattern
const uint32_t sword_frame[][4] = {
  { 0x00100100, 0x10010010, 0x01001001, 0x00100100 },
};

// Checkmark pattern (correct answer)
const uint32_t check_frame[][4] = {
  { 0x00000001, 0x00100100, 0x10010000, 0x00000000 },
};

// X pattern (wrong answer)
const uint32_t x_frame[][4] = {
  { 0x10010010, 0x01001001, 0x01001001, 0x10010010 },
};

// Heart pattern (victory)
const uint32_t heart_frame[][4] = {
  { 0x01101101, 0x11111111, 0x11111111, 0x01000010 },
};

// Skull pattern (defeat)
const uint32_t skull_frame[][4] = {
  { 0x01111110, 0x10100101, 0x01111110, 0x01010100 },
};

// All LEDs on
const uint32_t all_on[][4] = {
  { 0x11111111, 0x11111111, 0x11111111, 0x11111111 },
};

// All LEDs off
const uint32_t all_off[][4] = {
  { 0x00000000, 0x00000000, 0x00000000, 0x00000000 },
};


void flashPattern(const uint32_t frame[][4], int times, int on_ms, int off_ms) {
  for (int i = 0; i < times; i++) {
    matrix.loadFrame(frame[0]);
    delay(on_ms);
    matrix.loadFrame(all_off[0]);
    delay(off_ms);
  }
}

void swordClashAnimation() {
  // Quick alternating flashes to simulate sword clash
  for (int i = 0; i < 4; i++) {
    matrix.loadFrame(all_on[0]);
    delay(50);
    matrix.loadFrame(all_off[0]);
    delay(50);
  }
  matrix.loadFrame(sword_frame[0]);
  delay(500);
  matrix.loadFrame(all_off[0]);
}

void correctAnimation() {
  // Triumphant flash then checkmark
  matrix.loadFrame(all_on[0]);
  delay(100);
  matrix.loadFrame(all_off[0]);
  delay(100);
  flashPattern(check_frame, 3, 300, 200);
}

void wrongAnimation() {
  // Sad flicker then X
  flashPattern(x_frame, 3, 200, 200);
}

void victoryAnimation() {
  // Celebration: rapid flashes then heart
  for (int i = 0; i < 6; i++) {
    matrix.loadFrame(all_on[0]);
    delay(80);
    matrix.loadFrame(all_off[0]);
    delay(80);
  }
  // Hold heart pattern
  for (int i = 0; i < 5; i++) {
    matrix.loadFrame(heart_frame[0]);
    delay(400);
    matrix.loadFrame(all_off[0]);
    delay(200);
  }
}

void defeatAnimation() {
  // Slow fade-out effect then skull
  for (int i = 0; i < 3; i++) {
    matrix.loadFrame(all_on[0]);
    delay(300);
    matrix.loadFrame(all_off[0]);
    delay(300);
  }
  matrix.loadFrame(skull_frame[0]);
  delay(2000);
  matrix.loadFrame(all_off[0]);
}


void setup() {
  
  matrix.begin();
  matrix.clear();

  Bridge.begin();
  Bridge.provide("detection", fight);

  // Startup animation
  swordClashAnimation();

  Serial.println("=== Monkey Island Insult Sword Fight ===");
  Serial.println("MCU ready. Waiting for game events...");
}

void loop() {}

void fight() {

  swordClashAnimation();
  /*
  if (msg.length() > 0) {
    Serial.println("Event: " + msg);

    if (msg == "START") {
      swordClashAnimation();
    }
    else if (msg == "CORRECT") {
      correctAnimation();
    }
    else if (msg == "WRONG") {
      wrongAnimation();
    }
    else if (msg == "WIN") {
      victoryAnimation();
    }
    else if (msg == "LOSE") {
      defeatAnimation();
    }
  }*/

  delay(50);  // Small delay to prevent busy-waiting
}
