import time
import RPi.GPIO as GPIO


sdata_pin = 7       # (pin 26 = GPIO7)   = DATA
sclk_pin = 8        # (pin 24 = GPIO8)   = HODINY
reset_pin = 25      # (pin 22 = GPIO25)  = RESET

mapa={}             # pamet, do ktere se uklada aktualni stav zobrazenych pixelu na displeji
txtmapa={}          # pamet, do ktere se uklada aktualni stav textu na displeji
font2={}            # pamet, ve ktere je ulozeny font, nacetny z externiho souboru
ikodata={}          # promenna, pres kterou se budou definovat graficke ikony


def velky_napis(text, zn_x, radka):
    if (len(text) + zn_x > 16):  # pokud je na radce text delsi, nez 16 znaku,
        text = text[0:16 - zn_x]  # ... tak se konec odsekne

    txt_start(zn_x, radka)  # startovni poloha textu se posle do displeje
    for znak in range(len(text)):
        posli_bajt1(1, ord(text[znak:znak + 1]))  # znaky z textu se postupne posilaji do displeje
        pomtext = txtmapa[radka][:zn_x + znak] + text[znak:znak + 1] + txtmapa[radka][zn_x + znak + 1:]
        txtmapa[radka] = pomtext  # pamet pro textovy rezim

def txt_start(sloupec , radka):
  posun = sloupec
  if (radka == 1) : posun = sloupec + 32
  if (radka == 2) : posun = sloupec + 16
  if (radka == 3) : posun = sloupec + 48

  posli_bajt1( 0, 0b10000000 + int(posun / 2))  # Address Counter na pozadovanou pozici

  # pri lichem sloupci se musi napis doplnit o znak, ktery je na displeji pred nove tisknutym napisem 
  if (sloupec / 2.0 != sloupec/2):
    puvodni_predznak = txtmapa[radka][sloupec - 1:sloupec] # "predznak" se zjistuje z pomocne textove pameti
    posli_bajt1( 1, ord(puvodni_predznak)) 

def strobe():
    GPIO.output(sclk_pin, True)
    time.sleep(0.0000001)
    GPIO.output(sclk_pin, False)
    time.sleep(0.0000001)

def serd(bit):
  if (bit == 1):
     GPIO.output(sdata_pin, True)
  else:
     GPIO.output(sdata_pin, False)

def posli_bajt1(rs, bajt):
    serd(1)  # zacatek komunikace se provadi "synchro" sekvenci 5 jednicek
    for i in range(5):
        strobe()

    serd(0)  # pak se odesle RW bit (pri zapisu je nastaven na "0")
    strobe()
    serd(rs)  # pak se posle RS bit (prikazy = "0" ; data = "1")
    strobe()
    serd(0)  # nasleduje nulovy bit
    strobe()

    for i in range(7, 3, -1):  # a pak horni ctyri bity z odesilaneho bajtu
        bit = (bajt & (2 ** i)) >> i
        serd(bit)
        strobe()

    serd(0)  # potom se odesle oddelovaci sekvence 4x "0"
    for i in range(4):
        strobe()

    for i in range(3, -1, -1):  # po ni nasleduje zbytek dat (spodni 4 bity z odesilaneho bajtu)
        bit = (bajt & (2 ** i)) >> i
        serd(bit)
        strobe()

    serd(0)  # na zaver opet oddelovaci sekvence 4x "0"
    for i in range(4):
        strobe()


def posli_bajt2(rs, bajt1, bajt2):
    serd(1)  # zacatek komunikace se provadi "synchro" sekvenci 5 jednicek
    for i in range(5):
        strobe()

    serd(0)  # pak se odesle RW bit (pri zapisu je nastaven na "0")
    strobe()
    serd(rs)  # pak se posle RS bit (prikazy = "0" ; data = "1")
    strobe()
    serd(0)  # nasleduje nulovy bit
    strobe()

    for i in range(7, 3, -1):  # a pak horni ctyri bity z prvniho bajtu
        bit = (bajt1 & (2 ** i)) >> i
        serd(bit)
        strobe()

    serd(0)  # dale je oddelovaci sekvence 4x "0"
    for i in range(4):
        strobe()

    for i in range(3, -1, -1):  # a pak nasleduje zbytek z prvniho bajtu (nizsi 4 bity)
        bit = (bajt1 & (2 ** i)) >> i
        serd(bit)
        strobe()

    serd(0)  # potom je zase oddelovaci sekvence 4x "0"
    for i in range(4):
        strobe()

    # druhy bajt se odesila okamzite bez "hlavicky" (bez 5x "1" + RW bit + RS bit + "0")
    for i in range(7, 3, -1):  # i tento druhy bajt je rozdeleny na 2 casti (horni 4 bity)
        bit = (bajt2 & (2 ** i)) >> i
        serd(bit)
        strobe()

    serd(0)  # oddelovaci sekvence 4x "0"
    for i in range(4):
        strobe()

    for i in range(3, -1, -1):  # spodni 4 bity
        bit = (bajt2 & (2 ** i)) >> i
        serd(bit)
        strobe()

    serd(0)  # posledni oddelovaci sekvence 4x "0"
    for i in range(4):
        strobe()

def init():
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(sdata_pin, GPIO.OUT)    # (pin 26 = GPIO7)   = DATA
  GPIO.setup(sclk_pin, GPIO.OUT)     # (pin 24 = GPIO8)   = HODINY
  GPIO.setup(reset_pin, GPIO.OUT)    # (pin 22 = GPIO25)  = RESET

  GPIO.output(sdata_pin, False)      # DATA do "0"
  GPIO.output(sclk_pin, False)       # HODINY do "0"
  GPIO.output(reset_pin, False)      # RESET do "0"
  time.sleep(0.1)
  GPIO.output(reset_pin, True)       # RESET do "1"

def clr_text():
  posli_bajt1( 0, 0b00110000)  # function set (8 bit)
  posli_bajt1( 0, 0b00110000)  # function set (basic instr. set)
  posli_bajt1( 0, 0b00001100)  # displ.=ON , cursor=OFF , blik=OFF
  posli_bajt1( 0, 0b00000001)  # clear

  # vymazani pomocne textove pameti
  txtmapa[0] = "                "
  txtmapa[1] = "                "
  txtmapa[2] = "                "
  txtmapa[3] = "                "


def clr_grafika(pattern=0):
    init_grafika()
    posli_bajt1(0, 0b00110110)  # function set (extend instr.set)
    posli_bajt1(0, 0b00110100)  # function set (grafika OFF) - aby nebylo videt postupne mazani displeje
    posli_bajt1(0, 0b00001000)  # displ.=OFF , cursor=OFF , blik=OFF

    for vertikal in range(32):
        posli_bajt2(0, 0b10000000 + vertikal, 0b10000000)  # nastaveni adresy na displeji na zacatek mikroradky
        for horizontal in range(16):
            posli_bajt2(1, pattern, pattern)  # po dvojbajtech zaplni cely displej stejnym kodem

            # a tento kod se jeste zapise na jednotlive pozice do pomocne pameti
            mapa[horizontal, vertikal, 0] = pattern
            mapa[horizontal, vertikal, 1] = pattern

    posli_bajt1(0, 0b00110110)  # function set (grafika ON) - smazany displej se zobrazi okamzite

def disclear(pattern=0):
  clr_grafika(pattern)
  clr_text()

def init_grafika():
  posli_bajt1( 0, 0b00110010)  # function set (8 bit)
  posli_bajt1( 0, 0b00110110)  # function set (extend instr. set)
  posli_bajt1( 0, 0b00110110)  # function set (grafika ON)
  posli_bajt1( 0, 0b00000010)  # enable CGRAM po prenastaveni do BASIC instr.set

def init_text():
  posli_bajt1( 0, 0b00110000)  # function set (8 bit)
  posli_bajt1( 0, 0b00110100)  # function set (extend instr. set)
  posli_bajt1( 0, 0b00110110)  # function set (grafika OFF)
  posli_bajt1( 0, 0b00000010)  # enable CGRAM (po prenastaveni do BASIC instr.set)
  posli_bajt1( 0, 0b00110000)  # function set (basic instr. set)
  posli_bajt1( 0, 0b00001100)  # displ.=ON , cursor=OFF , blik=OFF
  posli_bajt1( 0, 0b10000000)  # Address Counter na levy horni roh

def defikon(ikona,ikodata):
  init_text()
  posli_bajt1( 0, 64 + (ikona * 16) )  # nastaveni adresy grafiky
  for dat in range(16):
    levy_bajt  = int(ikodata[dat] / 256)
    pravy_bajt = ikodata[dat] % 256
    posli_bajt2( 1, levy_bajt , pravy_bajt)

def printiko(cislo , x , y):
  posun = x
  if (y == 1) : posun = posun + 16
  if (y == 2) : posun = posun + 8
  if (y == 3) : posun = posun + 24
  posli_bajt1( 0, 0b10000000 + posun)  # Address Counter na pozadovanou pozici
  posli_bajt2( 1 ,  0 , cislo * 2)
