// WinAmp Physical Edition — RP2040 controls firmware.
//
// Implements the full serial protocol (docs/serial-protocol.md) over USB CDC:
//   in : FADER, FADER_RELEASE, LED, DISP TITLE/TIME/INFO, PING
//   out: EV BTN/FADER/TOUCH/ENC/POT/BAT/CHG/JACK, PONG, LOG
//
// I/O architecture (hardware/wiring.md): motors via 2x PCA9685 -> DRV8833,
// touch via MPR121, buttons via MCP23017, amp via TPA2016, battery via the
// X728's MAX17040 — all on one I2C bus. OLED readout on software SPI.
// Written desk-first (2026-07-16): compiles clean; PID gains + stiction floor
// need bench tuning with real faders.

#include <Arduino.h>
#include <Wire.h>

#include "config.h"

#if HAS_PCA9685
#include <Adafruit_PWMServoDriver.h>
#endif
#if HAS_MPR121
#include <Adafruit_MPR121.h>
#endif
#if HAS_MCP23017
#include <Adafruit_MCP23X17.h>
#endif
#if HAS_TPA2016
#include <Adafruit_TPA2016.h>
#endif
#if HAS_NEOPIXEL
#include <Adafruit_NeoPixel.h>
#endif
#if HAS_OLED
#include <U8g2lib.h>
#endif

// --------------------------------------------------------------------------- //
// devices (presence-flagged so a missing board degrades, never hangs)
// --------------------------------------------------------------------------- //
#if HAS_PCA9685
Adafruit_PWMServoDriver pcaA(ADDR_PCA_A);
Adafruit_PWMServoDriver pcaB(ADDR_PCA_B);
bool havePcaA = false, havePcaB = false;
#endif
#if HAS_MPR121
Adafruit_MPR121 touch;
bool haveTouch = false;
#endif
#if HAS_MCP23017
Adafruit_MCP23X17 mcp;
bool haveMcp = false;
#endif
#if HAS_TPA2016
Adafruit_TPA2016 amp;
bool haveAmp = false;
#endif
#if HAS_NEOPIXEL
Adafruit_NeoPixel pixels(NUM_PIXELS, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
#endif
#if HAS_OLED
U8G2_SSD1322_NHD_256X64_F_4W_SW_SPI oled(U8G2_R0, PIN_OLED_SCK, PIN_OLED_MOSI,
                                         PIN_OLED_CS, PIN_OLED_DC, PIN_OLED_RST);
bool haveOled = false;
#endif

// --------------------------------------------------------------------------- //
// state
// --------------------------------------------------------------------------- //
struct Fader {
  int16_t  target = -1;        // -1 = released (user owns it)
  float    pos = 0;            // filtered position, 0..1023
  float    prevErr = 0;
  bool     touched = false;
  uint16_t lastReported = 0xFFFF;
};
Fader faders[NUM_FADERS];

uint16_t balanceLast = 0xFFFF;
uint16_t buttonsLast = 0xFFFF;   // MCP GPIOAB snapshot (pull-ups: 1 = released)
uint32_t buttonsChangedAt[16] = {0};
bool     jackLast = false;

int8_t  encAccum[2] = {0, 0};
uint8_t encPrev[2] = {0, 0};
bool    encSwLast[2] = {true, true};

char  dispTitle[96] = "WINAMP · PHYSICAL EDITION";
uint32_t dispPosMs = 0, dispDurMs = 0;
uint16_t dispKbps = 0, dispKhz = 0;
uint32_t dispPosStamp = 0;       // millis() when dispPosMs was set
int16_t  marqueeX = 0;

// --------------------------------------------------------------------------- //
// serial protocol
// --------------------------------------------------------------------------- //
static void emit(const char* type, int id, long value) {
  Serial.print("EV "); Serial.print(type); Serial.print(' ');
  Serial.print(id); Serial.print(' '); Serial.println(value);
}
static void logmsg(const char* msg) { Serial.print("LOG "); Serial.println(msg); }

static char rxBuf[160];
static uint8_t rxLen = 0;

static void handleDisp(char* args) {
  char* what = strtok(args, " ");
  if (!what) return;
  if (!strcmp(what, "TITLE")) {
    char* rest = strtok(nullptr, "");            // remainder incl. spaces
    strncpy(dispTitle, rest ? rest : "-", sizeof(dispTitle) - 1);
    dispTitle[sizeof(dispTitle) - 1] = 0;
    marqueeX = 0;
  } else if (!strcmp(what, "TIME")) {
    dispPosMs = strtoul(strtok(nullptr, " ") ?: "0", nullptr, 10);
    dispDurMs = strtoul(strtok(nullptr, " ") ?: "0", nullptr, 10);
    dispPosStamp = millis();
  } else if (!strcmp(what, "INFO")) {
    dispKbps = atoi(strtok(nullptr, " ") ?: "0");
    dispKhz  = atoi(strtok(nullptr, " ") ?: "0");
  }
}

static void handleCommand(char* line) {
  char* verb = strtok(line, " ");
  if (!verb) return;
  if (!strcmp(verb, "PING")) {
    Serial.println("PONG");
  } else if (!strcmp(verb, "FADER")) {
    int id = atoi(strtok(nullptr, " ") ?: "-1");
    int pos = atoi(strtok(nullptr, " ") ?: "0");
    if (id >= 0 && id < NUM_FADERS)
      faders[id].target = constrain(pos, 0, (int)FADER_MAX);
  } else if (!strcmp(verb, "FADER_RELEASE")) {
    int id = atoi(strtok(nullptr, " ") ?: "-1");
    if (id >= 0 && id < NUM_FADERS) faders[id].target = -1;
  } else if (!strcmp(verb, "LED")) {
#if HAS_NEOPIXEL
    int i = atoi(strtok(nullptr, " ") ?: "0");
    int r = atoi(strtok(nullptr, " ") ?: "0");
    int g = atoi(strtok(nullptr, " ") ?: "0");
    int b = atoi(strtok(nullptr, " ") ?: "0");
    if (i >= 0 && i < (int)NUM_PIXELS) {
      pixels.setPixelColor(i, pixels.Color(r, g, b));
      pixels.show();
    }
#endif
  } else if (!strcmp(verb, "DISP")) {
    handleDisp(strtok(nullptr, ""));
  }
}

static void pollSerial() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (rxLen) { rxBuf[rxLen] = 0; handleCommand(rxBuf); rxLen = 0; }
    } else if (rxLen < sizeof(rxBuf) - 1) {
      rxBuf[rxLen++] = c;
    } else {
      rxLen = 0;  // overlong line: drop it
    }
  }
}

// --------------------------------------------------------------------------- //
// analog mux
// --------------------------------------------------------------------------- //
static uint16_t readMux(uint8_t channel) {
  for (uint8_t i = 0; i < 4; i++) digitalWrite(PIN_MUX_S[i], (channel >> i) & 1);
  delayMicroseconds(8);                 // mux + RC settle
  return analogRead(PIN_MUX_ADC);       // 10-bit, 0..1023
}

// --------------------------------------------------------------------------- //
// motors (PCA9685 -> DRV8833). Fader f uses channels f*2 / f*2+1.
// --------------------------------------------------------------------------- //
static void motorRaw(uint8_t f, uint16_t in1, uint16_t in2) {
#if HAS_PCA9685
  uint8_t chan = (f * 2) % 16;
  Adafruit_PWMServoDriver* p = (f < 8) ? &pcaA : &pcaB;
  bool have = (f < 8) ? havePcaA : havePcaB;
  if (!have) return;
  p->setPin(chan, in1, false);
  p->setPin(chan + 1, in2, false);
#endif
}
static void motorOff(uint8_t f) { motorRaw(f, 0, 0); }  // coast

static void motorDrive(uint8_t f, float effort) {
  // effort in [-1, 1]; map through the stiction floor so small efforts move.
  if (effort == 0) { motorOff(f); return; }
  uint16_t mag = (uint16_t)(PWM_MIN_MOVE + fabsf(effort) * (PWM_MAX - PWM_MIN_MOVE));
  if (mag > PWM_MAX) mag = PWM_MAX;
  if (effort > 0) motorRaw(f, mag, 0);
  else            motorRaw(f, 0, mag);
}

// --------------------------------------------------------------------------- //
// subsystem tasks
// --------------------------------------------------------------------------- //
static void taskControl() {           // PID_HZ
  static const float dt = 1.0f / PID_HZ;
  for (uint8_t f = 0; f < NUM_FADERS; f++) {
    uint16_t raw = readMux(f);
    Fader& fd = faders[f];
    fd.pos += 0.5f * ((float)raw - fd.pos);        // light EMA filter

    if (fd.touched || fd.target < 0) {
      motorOff(f);
      uint16_t p = (uint16_t)fd.pos;
      if (abs((int)p - (int)fd.lastReported) > REPORT_DELTA) {
        emit("FADER", f, p);
        fd.lastReported = p;
      }
      fd.prevErr = 0;
      continue;
    }
    float err = (float)fd.target - fd.pos;
    if (fabsf(err) <= PID_DEADBAND) { motorOff(f); fd.prevErr = 0; continue; }
    float deriv = (err - fd.prevErr) / dt;
    fd.prevErr = err;
    float effort = (PID_KP * err + PID_KD * deriv) / (float)FADER_MAX;
    motorDrive(f, constrain(effort, -1.0f, 1.0f));
  }
  // balance pot
  uint16_t bal = readMux(MUX_CH_BALANCE);
  if (balanceLast == 0xFFFF || abs((int)bal - (int)balanceLast) > REPORT_DELTA) {
    emit("POT", 0, bal);
    balanceLast = bal;
  }
}

static void taskTouch() {             // ~100 Hz
#if HAS_MPR121
  if (!haveTouch) return;
  uint16_t t = touch.touched();
  for (uint8_t f = 0; f < NUM_FADERS; f++) {
    bool now = t & (1u << f);
    if (now != faders[f].touched) {
      faders[f].touched = now;
      if (now) motorOff(f);
      emit("TOUCH", f, now ? 1 : 0);
    }
  }
#endif
}

static void taskButtons() {           // ~200 Hz, 8 ms debounce
#if HAS_MCP23017
  if (!haveMcp) return;
  uint16_t gpio = mcp.readGPIOAB();
  uint32_t now = millis();
  if (buttonsLast == 0xFFFF) { buttonsLast = gpio; return; }
  for (uint8_t i = 0; i <= NUM_BUTTONS; i++) {   // 0-12 buttons; 15 = jack below
    if (i >= 16) break;
    bool was = !(buttonsLast & (1u << i));       // active-low (pull-ups)
    bool is  = !(gpio & (1u << i));
    if (was != is && now - buttonsChangedAt[i] > 8) {
      buttonsChangedAt[i] = now;
      if (i < NUM_BUTTONS) emit("BTN", i, is ? 1 : 0);
    }
  }
  bool jack = !(gpio & (1u << MCP_PIN_JACK));    // inserted = closed to GND
  if (jack != jackLast) {
    jackLast = jack;
    emit("JACK", 0, jack ? 1 : 0);
#if HAS_TPA2016
    if (haveAmp) amp.enableChannel(!jack, !jack);   // headphones in -> speakers off
#endif
  }
  buttonsLast = gpio;
#endif
}

static void pollEncoders() {          // every loop pass (fast)
  static const int8_t table[16] = {0,-1,1,0, 1,0,0,-1, -1,0,0,1, 0,1,-1,0};
  const uint8_t pinsA[2] = {PIN_ENC1_A, PIN_ENC2_A};
  const uint8_t pinsB[2] = {PIN_ENC1_B, PIN_ENC2_B};
  const uint8_t pinsS[2] = {PIN_ENC1_SW, PIN_ENC2_SW};
  const uint8_t btnIds[2] = {BTN_ENC1_PUSH, BTN_ENC2_PUSH};
  for (uint8_t e = 0; e < 2; e++) {
    uint8_t cur = (digitalRead(pinsA[e]) << 1) | digitalRead(pinsB[e]);
    if (cur != encPrev[e]) {
      encAccum[e] += table[(encPrev[e] << 2) | cur];
      encPrev[e] = cur;
    }
    bool sw = digitalRead(pinsS[e]);           // active low
    if (sw != encSwLast[e]) {
      encSwLast[e] = sw;
      emit("BTN", btnIds[e], sw ? 0 : 1);
    }
  }
}

static void taskEncoderReport() {     // ~20 Hz: 4 steps = 1 detent on EC11/PEC11
  for (uint8_t e = 0; e < 2; e++) {
    int8_t detents = encAccum[e] / 4;
    if (detents != 0) {
      encAccum[e] -= detents * 4;
      emit("ENC", e, detents);
    }
  }
}

static void taskBattery() {           // every 5 s
#if HAS_MAX17040
  Wire.beginTransmission(ADDR_MAX17040);
  Wire.write(0x04);                              // SOC register
  if (Wire.endTransmission(false) != 0) return;  // gauge absent — stay quiet
  if (Wire.requestFrom((int)ADDR_MAX17040, 2) != 2) return;
  uint8_t hi = Wire.read(), lo = Wire.read();
  uint16_t socX10 = (uint16_t)hi * 10 + ((uint16_t)lo * 10) / 256;
  if (socX10 > 1000) socX10 = 1000;
  emit("BAT", 0, socX10);
  emit("CHG", 0, digitalRead(PIN_X728_PLD) ? 1 : 0);
#endif
}

static void taskDisplay() {           // ~10 Hz
#if HAS_OLED
  if (!haveOled) return;
  // live position estimate between DISP TIME updates
  uint32_t pos = dispPosMs;
  if (dispDurMs > 0 && dispPosStamp) pos += millis() - dispPosStamp;
  if (dispDurMs > 0 && pos > dispDurMs) pos = dispDurMs;

  char timeStr[12];
  snprintf(timeStr, sizeof(timeStr), "%lu:%02lu",
           (unsigned long)(pos / 60000), (unsigned long)((pos / 1000) % 60));

  oled.clearBuffer();
  oled.setFont(u8g2_font_logisoso28_tn);          // big elapsed time
  oled.drawStr(0, 32, timeStr);

  oled.setFont(u8g2_font_7x13B_tr);               // scrolling title
  int16_t tw = oled.getStrWidth(dispTitle);
  if (tw <= 256) {
    oled.drawStr(0, 60, dispTitle);
  } else {
    marqueeX -= 2;
    if (marqueeX < -(tw + 40)) marqueeX = 0;
    oled.drawStr(marqueeX, 60, dispTitle);
    oled.drawStr(marqueeX + tw + 40, 60, dispTitle);
  }
  if (dispKbps) {                                 // stream info, top right
    char info[24];
    snprintf(info, sizeof(info), "%uk %ukHz", dispKbps, dispKhz);
    oled.setFont(u8g2_font_6x10_tr);
    oled.drawStr(256 - oled.getStrWidth(info), 10, info);
  }
  oled.sendBuffer();
#endif
}

// --------------------------------------------------------------------------- //
// setup / loop
// --------------------------------------------------------------------------- //
void setup() {
  Serial.begin(115200);

  pinMode(PIN_PCA_OE, OUTPUT);
  digitalWrite(PIN_PCA_OE, HIGH);      // motors DISABLED until PCA configured
  pinMode(PIN_X728_PLD, INPUT_PULLUP);
  for (uint8_t i = 0; i < 4; i++) pinMode(PIN_MUX_S[i], OUTPUT);
  analogReadResolution(10);
  const uint8_t encPins[6] = {PIN_ENC1_A, PIN_ENC1_B, PIN_ENC1_SW,
                              PIN_ENC2_A, PIN_ENC2_B, PIN_ENC2_SW};
  for (uint8_t i = 0; i < 6; i++) pinMode(encPins[i], INPUT_PULLUP);

  Wire.begin();                        // GP4/GP5
  Wire.setClock(400000);

#if HAS_PCA9685
  havePcaA = pcaA.begin();
  havePcaB = pcaB.begin();
  for (uint8_t p = 0; p < 2; p++) {
    Adafruit_PWMServoDriver* d = p ? &pcaB : &pcaA;
    if (!(p ? havePcaB : havePcaA)) continue;
    d->setOscillatorFrequency(27000000);
    d->setPWMFreq(1526);               // max — least audible motor buzz
    for (uint8_t c = 0; c < 16; c++) d->setPin(c, 0, false);
  }
  if (havePcaA || havePcaB) digitalWrite(PIN_PCA_OE, LOW);   // outputs now safe
  logmsg(havePcaA ? "pcaA ok" : "pcaA MISSING");
  logmsg(havePcaB ? "pcaB ok" : "pcaB MISSING");
#endif
#if HAS_MPR121
  haveTouch = touch.begin(ADDR_MPR121, &Wire);
  logmsg(haveTouch ? "mpr121 ok" : "mpr121 MISSING");
#endif
#if HAS_MCP23017
  haveMcp = mcp.begin_I2C(ADDR_MCP23017, &Wire);
  if (haveMcp)
    for (uint8_t i = 0; i < 16; i++) mcp.pinMode(i, INPUT_PULLUP);
  logmsg(haveMcp ? "mcp23017 ok" : "mcp23017 MISSING");
#endif
#if HAS_TPA2016
  haveAmp = amp.begin(ADDR_TPA2016, &Wire);
  if (haveAmp) { amp.enableChannel(true, true); amp.setGain(6); }
  logmsg(haveAmp ? "tpa2016 ok" : "tpa2016 MISSING");
#endif
#if HAS_NEOPIXEL
  pixels.begin();
  pixels.clear();
  pixels.show();
#endif
#if HAS_OLED
  haveOled = oled.begin();
  logmsg(haveOled ? "oled ok" : "oled MISSING");
#endif
  logmsg("winamp-fw ready");
}

void loop() {
  static uint32_t tControl = 0, tTouch = 0, tButtons = 0, tEncRep = 0,
                  tDisplay = 0, tBattery = 0;
  uint32_t now = millis();

  pollSerial();
  pollEncoders();                                 // every pass — quadrature

  if (now - tControl >= (1000 / PID_HZ)) { tControl = now; taskControl(); }
  if (now - tTouch   >= 10)   { tTouch = now;   taskTouch(); }
  if (now - tButtons >= 5)    { tButtons = now; taskButtons(); }
  if (now - tEncRep  >= 50)   { tEncRep = now;  taskEncoderReport(); }
  if (now - tDisplay >= 100)  { tDisplay = now; taskDisplay(); }
  if (now - tBattery >= 5000) { tBattery = now; taskBattery(); }
}
