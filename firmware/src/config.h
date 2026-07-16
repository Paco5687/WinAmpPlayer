// WinAmp Physical Edition — RP2040 firmware configuration.
// Pin assignments mirror hardware/diagrams/pico-pinout.svg — keep them in sync.
#pragma once

#include <Arduino.h>

// ---- feature flags (disable subsystems during bench bring-up) -------------- //
#define HAS_PCA9685   1   // motor PWM (2x, I2C)
#define HAS_MPR121    1   // fader touch-sense
#define HAS_MCP23017  1   // panel buttons + jack detect
#define HAS_TPA2016   1   // speaker amp
#define HAS_MAX17040  1   // X728 fuel gauge (jumpered onto our I2C bus)
#define HAS_OLED      1   // SSD1322 256x64 readout
#define HAS_NEOPIXEL  1

// ---- pins (see pico-pinout.svg) -------------------------------------------- //
// I2C0 (Wire) uses the arduino-pico defaults: SDA=GP4, SCL=GP5.
static const uint8_t PIN_X728_PLD   = 2;    // X728 AC-loss / charge detect
static const uint8_t PIN_PCA_OE     = 3;    // PCA9685 /OE — HIGH = motors disabled
static const uint8_t PIN_MUX_S[4]   = {6, 7, 8, 9};
static const uint8_t PIN_OLED_SCK   = 10;   // software SPI
static const uint8_t PIN_OLED_MOSI  = 11;
static const uint8_t PIN_OLED_DC    = 12;
static const uint8_t PIN_OLED_CS    = 13;
static const uint8_t PIN_OLED_RST   = 14;
static const uint8_t PIN_ENC1_A     = 16;
static const uint8_t PIN_ENC1_B     = 17;
static const uint8_t PIN_ENC1_SW    = 18;
static const uint8_t PIN_ENC2_A     = 19;
static const uint8_t PIN_ENC2_B     = 20;
static const uint8_t PIN_ENC2_SW    = 21;
static const uint8_t PIN_NEOPIXEL   = 22;
static const uint8_t PIN_MUX_ADC    = 26;   // ADC0 <- mux common

// ---- I2C addresses (see hardware/wiring.md address map) -------------------- //
static const uint8_t ADDR_PCA_A     = 0x40; // motors 0-7 (channels 0-15)
static const uint8_t ADDR_PCA_B     = 0x41; // motors 8-9 (channels 0-3)
static const uint8_t ADDR_MCP23017  = 0x20;
static const uint8_t ADDR_MAX17040  = 0x36;
static const uint8_t ADDR_TPA2016   = 0x58;
static const uint8_t ADDR_MPR121    = 0x5A;

// ---- controls --------------------------------------------------------------- //
static const uint8_t NUM_FADERS     = 10;   // 0-6 EQ, 7 preamp, 8 volume, 9 seek
static const uint8_t NUM_BUTTONS    = 13;   // ButtonId 0-12 on MCP pins 0-12
static const uint8_t MCP_PIN_JACK   = 15;   // headphone jack detect (switched TRS)
static const uint8_t BTN_ENC1_PUSH  = 13;   // encoder pushes emit these button ids
static const uint8_t BTN_ENC2_PUSH  = 14;
static const uint8_t MUX_CH_BALANCE = 10;   // wipers 0-9 = faders, 10 = balance pot
static const uint8_t NUM_PIXELS     = 8;

// ---- tuning ----------------------------------------------------------------- //
static const uint16_t FADER_MAX     = 1023; // protocol position range
static const uint16_t PID_HZ        = 250;  // control loop rate
static const float    PID_KP        = 3.0f; // effort per count of error (tune!)
static const float    PID_KD        = 0.8f;
static const uint16_t PID_DEADBAND  = 8;    // counts — close enough, motor off
static const uint16_t REPORT_DELTA  = 5;    // counts — user-move report threshold
static const uint16_t PWM_MAX       = 4095; // PCA9685 full scale
static const uint16_t PWM_MIN_MOVE  = 900;  // stiction floor (tune on bench)
