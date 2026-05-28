from machine import Pin, SoftI2C
import time
import ssd1306

# --- 1. CONFIGURACIÓN DE PINES BCD ---
PIN_D0, PIN_D1, PIN_D2, PIN_D3 = 14, 13, 12, 5
PIN_D4, PIN_D5, PIN_D6, PIN_D7 = 6, 7, 8, 9
PIN_RST_B, PIN_RST_A, PIN_EN_A = 10, 11, 15
PIN_LED = 25

# --- 2. PIN DE CONTROL (GPIO 4) ---
pin_control = Pin(4, Pin.OUT)
pin_control.value(1)
# Guardamos el tiempo de inicio para el temporizador de 10s
inicio_programa = time.ticks_ms()
pin_activo = True

# --- 3. CONFIGURACIÓN OLED ---
i2c = SoftI2C(sda=Pin(20), scl=Pin(21), freq=100000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# --- 4. INICIALIZACIÓN HARDWARE CD4518 ---
en_a  = Pin(PIN_EN_A,  Pin.OUT, value=1)
rst_a = Pin(PIN_RST_A, Pin.OUT, value=0)
rst_b = Pin(PIN_RST_B, Pin.OUT, value=0)
d_pins = [Pin(p, Pin.IN) for p in [PIN_D0, PIN_D1, PIN_D2, PIN_D3, PIN_D4, PIN_D5, PIN_D6, PIN_D7]]
led = Pin(PIN_LED, Pin.OUT, value=0)

carry_count = 0
def irq_handler(pin):
    global carry_count
    carry_count += 1

carry = Pin(PIN_D7, Pin.IN)
carry.irq(trigger=Pin.IRQ_FALLING, handler=irq_handler)

# --- 5. FUNCIONES ---
def read_bcd():
    u = (d_pins[0].value() | (d_pins[1].value() << 1) | (d_pins[2].value() << 2) | (d_pins[3].value() << 3))
    t = (d_pins[4].value() | (d_pins[5].value() << 1) | (d_pins[6].value() << 2) | (d_pins[7].value() << 3))
    if u > 9 or t > 9: return None
    return (t * 10) + u

def actualizar_oled(valor_hz, pin_state):
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.fill_rect(0, 0, 128, 15, 1)
    oled.text("FRECUENCIMETRO", 8, 4, 0)
    
    oled.text("Lectura:", 10, 22)
    oled.text("{:7d} Hz".format(valor_hz), 25, 35)
    
    # Estado del GPIO 4 en pantalla
    status = "GPIO4: ON" if pin_state else "GPIO4: OFF"
    oled.text(status, 10, 50)
    oled.show()

# --- 6. BUCLE PRINCIPAL ---
GATE_MS = 1000
gate_start = time.ticks_ms()

print("GPIO 4 en ALTO. Bajará en 10 segundos...")

while True:
    now = time.ticks_ms()

    # --- CONTROL TEMPORIZADO DEL GPIO 4 ---
    if pin_activo and time.ticks_diff(now, inicio_programa) >= 10000:
        pin_control.value(0)
        pin_activo = False
        print("GPIO 4 cambiado a BAJO.")

    # Destello de actividad en el LED
    led.value(1 if (now % 1000) < 100 else 0)

    # --- PROCESO DE MEDICIÓN (Cada 1 segundo) ---
    if time.ticks_diff(now, gate_start) >= GATE_MS:
        en_a.value(0) 
        
        bcd = read_bcd()
        cc = carry_count
        
        # Reset de hardware
        rst_a.value(1); rst_b.value(1)
        carry_count = 0
        time.sleep_us(10)
        rst_a.value(0); rst_b.value(0)
        en_a.value(1)
        
        if bcd is not None:
            frecuencia = (cc * 100) + bcd
            actualizar_oled(frecuencia, pin_activo)
        else:
            oled.fill(0)
            oled.text("ERROR BCD", 30, 30)
            oled.show()
            
        gate_start = time.ticks_ms()