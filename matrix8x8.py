```python
import pyb

class Matrix8x8:
    """
    Ovladač displeje 8x8 LED maticové s HT16K33 přídavným modulem od AdaFruit.
    Příklad použití:

    display = Matrix8x8()
    display.set(b'\xFF' * 8)    # zapnout všechny LED
    display.clear()             # vypnout všechny LED
    display.set_row(2, 0xFF)    # zapnout všechny LED ve 2. řádku
    display.set_column(3, 0xFF) # zapnout všechny LED ve 3. sloupci
    display.set_pixel(7, 6)     # zapnout LED na řádku 7, sloupec 6
    """
    row_addr = (0x00, 0x02, 0x04, 0x06, 0x08, 0x0A, 0x0C, 0x0E)

    def __init__(self, i2c_bus=1, addr=0x70, brightness=15, i2c=None):
        """
        Parametry:
        * i2c_bus = ID sběrnice I2C (1 nebo 2) nebo None (pokud je zadán parametr 'i2c')
        * addr = I2C adresa připojeného displeje
        * brightness = jas displeje (0 - 15)
        * i2c = inicializovaná instance objektu pyb.I2C
        """
        self._blinking = 0
        self.addr = addr
        self.buf = bytearray(8)

        # inicializace I2C
        if i2c:
            self.i2c = i2c
        else:
            self.i2c = pyb.I2C(i2c_bus, pyb.I2C.MASTER, baudrate=400000)

        # zapnutí oscilátoru HT16K33
        self._send(0x21)

        self.set_brightness(brightness)
        self.clear()
        self.on()

    def _send(self, data):
        """
        Odeslat data přes I2C.
        """
        self.i2c.send(data, self.addr)

    def _send_row(self, row):
        """
        Odeslat jednotlivý řádek přes I2C.
        """
        data = bytes((self.row_addr[row], rotate_right(self.buf[row])))
        self._send(data)

    def _send_buf(self):
        """
        Odeslat buffer přes I2C.
        """
        data = bytearray(16)
        i = 1
        for byte in self.buf:
            data[i] = rotate_right(byte)
            i += 2
        self._send(data)

    def _clear_column(self, column):
        """
        Vymazat sloupec v bufferu (nastavit na 0).
        """
        mask = 0x80 >> column
        for row in range(8):
            if self.buf[row] & mask:
                self.buf[row] ^= mask

    def _set_column(self, column, byte):
        """
        Nastavit sloupec v bufferu pomocí bytu.
        """
        self._clear_column(column)
        if byte == 0:
            return
        mask = 0x80
        for row in range(8):
            shift = column - row
            if shift >= 0:
                self.buf[row] |= (byte & mask) >> shift
            else:
                self.buf[row] |= (byte & mask) << abs(shift)
            mask >>= 1

    def on(self):
        """
        Zapnout displej.
        """
        self.is_on = True
        self._send(0x81 | self._blinking << 1)

    def off(self):
        """
        Vypnout displej. Lze ovládat displej, když je vypnutý (změna obrázku,
        jas, blikání, ...).
        """
        self.is_on = False
        self._send(0x80)

    def set_brightness(self, value):
        """
        Nastavit jas displeje. Hodnota od 0 (min) do 15 (max).
        """
        self._send(0xE0 | value)

    def set_blinking(self, mode):
        """
        Nastavit blikání. Režimy:
            0 - blikání vypnuto
            1 - blikání 2 Hz
            2 - blikání 1 Hz
            3 - blikání 0.5 Hz
        """
        self._blinking = mode
        if self.is_on:
            self.on()

    def set(self, bitmap):
        """
        Zobrazit bitmapu na displeji. Bitmapa by měla být objekt typu bytearray
        obsahující 8 bytů nebo jakýkoli iterovatelný objekt obsahující 8 bytů
        (jeden byte na řádek).
        """
        self.buf = bytearray(bitmap)
        self._send_buf()

    def clear(self):
        """
        Vymazat displej.
        """
        for i in range(8):
            self.buf[i] = 0
        self._send_buf()

    def set_row(self, row, byte):
        """
        Nastavit řádek pomocí bytu.
        """
        self.buf[row] = byte
        self._send_row(row)

    def clear_row(self, row):
        """
        Vymazat řádek.
        """
        self.set_row(row, 0)

    def set_column(self, column, byte):
        """
        Nastavit sloupec pomocí bytu.
        """
        self._set_column(column, byte)
        self._send_buf()

    def clear_column(self, column):
        """
        Vymazat sloupec.
        """
        self._clear_column(column)
        self._send_buf()

    def set_pixel(self, row, column):
        """
        Nastavit (zapnout) pixel.
        """
        self.buf[row] |= (0x80 >> column)
        self._send_row(row)

    def clear_pixel(self, row, column):
        """
        Vymazat pixel.
        """
        self.buf[row] &= ~(0x80 >> column)
        self._send_row(row)


def rotate_right(byte):
    """
    Rotovat bity doprava.
    """
    byte &= 0xFF
    bit = byte & 0x01
    byte >>= 1
    if bit:
        byte |= 0x80
    return byte

