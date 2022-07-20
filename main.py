# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////
# Import modules, widgets, library
import serial
import struct
import os
import sys
import glob
import platform
import time
# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from modules import *
from widgets import *
os.environ["QT_FONT_DPI"] = "96" # FIX Problem for High DPI and Scale above 100%
#-------------------------------------------------------------------------------


# Define macro
Flash_HAL_OK                                        = 0x00
Flash_HAL_ERROR                                     = 0x01
Flash_HAL_BUSY                                      = 0x02
Flash_HAL_TIMEOUT                                   = 0x03
Flash_HAL_INV_ADDR                                  = 0x04

COMMAND_BL_GET_VER                                  = 0x51
COMMAND_BL_GET_CID                                  = 0x53
COMMAND_BL_GO_TO_ADDR                               = 0x55
COMMAND_BL_MEM_WRITE                                = 0x57
COMMAND_BL_FLASH_ERASE                              = 0x56
COMMAND_BL_EN_R_W_PROTECT                           = 0x58
COMMAND_BL_READ_SECTOR_P_STATUS                     = 0x5A
COMMAND_BL_DIS_R_W_PROTECT                          = 0x5C

COMMAND_BL_GET_VER_LEN                              = 6
COMMAND_BL_GET_CID_LEN                              = 6
COMMAND_BL_GO_TO_ADDR_LEN                           = 10
COMMAND_BL_MEM_WRITE_LEN                            = 11
COMMAND_BL_FLASH_ERASE_LEN                          = 8
COMMAND_BL_EN_R_W_PROTECT_LEN                       = 8
COMMAND_BL_READ_SECTOR_P_STATUS_LEN                 = 6
COMMAND_BL_DIS_R_W_PROTECT_LEN                      = 6

verbose_mode = 1
mem_write_active =0

protection_mode= [ "Write Protection", "Read/Write Protection","No protection" ]
currentState = ""

#-------------------------------------------------------------------------------
#----------------------------- file ops----------------------------------------

def calc_file_len(path):
    size = os.path.getsize(path)
    return size
def open_the_file(path):
    global bin_file
    bin_file = open(path,'rb')
def read_the_file():
    pass
def close_the_file():
    bin_file.close()
def openDialog(self):    
    fileName = QFileDialog.getOpenFileName(self, 'Open Files', "", "")        
    #fileName = QFileDialog.getOpenFileName(widgets, Optional[str] = None, str = '', str = '', str = '', QFileDialog.Options = Default(QFileDialog.Options))
    print(fileName[0])
    widgets.lineEdit.setText(fileName[0])
#----------------------------- utilities----------------------------------------
def word_to_byte(addr, index , lowerfirst):
    value = (addr >> ( 8 * ( index -1)) & 0x000000FF )
    return value  
def get_crc(buff, length):
    Crc = 0xFFFFFFFF
    for data in buff[0:length]:
        Crc = Crc ^ data
        for i in range(32):
            if(Crc & 0x80000000):
                Crc = (Crc << 1) ^ 0x04C11DB7
            else:
                Crc = (Crc << 1)
    return Crc
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result
def Serial_Port_Configuration(port):
    global ser
    try:
        ser = serial.Serial(port,115200, timeout=3)
    except:
        print("\n   Oops! That was not a valid port")
        
        port = serial_ports()
        if(not port):
            print("\n   No ports Detected")
        else:
            print("\n   Here are some available ports on your PC. Try Again!")
            print("\n   ",port)
            widgets.lineEdit.setText("Invalid port. Let's try " + str(port))
            
        return -1
    if ser.is_open:
        widgets.lineEdit.setText("Open port successfully!!!")
        print("Open port successfully")
    else:
        widgets.lineEdit.setText("Open port failed")
        print("\n   Port Open Failed")
    return 0
def Close_serial_port(com):
    #port = serial_ports()
    #print("\n   ", port, com)
    global ser 
    ser.close()
    widgets.lineEdit.setText("Closed Com Port")
def read_serial_port(length):
    read_value = ser.read(length)
    return read_value
def listComPort():
    print("Jumped into list com port")
    port = serial_ports()
    if(not port):
        print("\n   No ports Detected")
        #widgets.lineEdit.setText("No port detected")
        widgets.comboBox2.setItemText(1, QCoreApplication.translate("MainWindow", u"No port detected", None))
    else:
        print("\n   Here are some available ports on your PC. Try Again!")
        print("\n   ",port)
        #widgets.lineEdit.setText("Select Com PORT")
        #temp1 = str(port)
        temp2 = port[0]
        #widgets.comboBox2.setItemText(1, QCoreApplication.translate("MainWindow", str(port), None))
        #print("\n   ",temp2)
        widgets.comboBox2.setItemText(1, QCoreApplication.translate("MainWindow", str(temp2), None))
        
def purge_serial_port():
    ser.reset_input_buffer()   
def Write_to_serial_port(value, *length):
    data = struct.pack('>B', value)
    if (verbose_mode):
        value = bytearray(data)
        #print("   "+hex(value[0]), end='')
        print("   "+"0x{:02x}".format(value[0]),end=' ')
    if(mem_write_active and (not verbose_mode)):
            print("#",end=' ')
    ser.write(data)
def portInit(com): 
    #print("Jumped to port init function")
    ret = 0
    ret = Serial_Port_Configuration(com)
    if (ret < 0):
        print("Invalid port")

    
    
#-------------------------------------------------------------------------------
# Process function
def process_COMMAND_BL_GO_TO_ADDR(length):
    addr_status=0
    value = read_serial_port(length)
    addr_status = bytearray(value)
    print("\n   Address Status : ",hex(addr_status[0]))
def process_COMMAND_BL_MEM_WRITE(length):
    write_status=0
    value = read_serial_port(length)
    write_status = bytearray(value)
    if(write_status[0] == Flash_HAL_OK):
        print("\n   Write_status: FLASH_HAL_OK")
    elif(write_status[0] == Flash_HAL_ERROR):
        print("\n   Write_status: FLASH_HAL_ERROR")
    elif(write_status[0] == Flash_HAL_BUSY):
        print("\n   Write_status: FLASH_HAL_BUSY")
    elif(write_status[0] == Flash_HAL_TIMEOUT):
        print("\n   Write_status: FLASH_HAL_TIMEOUT")
    elif(write_status[0] == Flash_HAL_INV_ADDR):
        print("\n   Write_status: FLASH_HAL_INV_ADDR")
    else:
        print("\n   Write_status: UNKNOWN_ERROR")
    print("\n")
def process_COMMAND_BL_FLASH_ERASE(length):
    erase_status=0
    value = read_serial_port(length)
    if len(value):
        erase_status = bytearray(value)
        if(erase_status[0] == Flash_HAL_OK):
            print("\n   Erase Status: Success  Code: FLASH_HAL_OK")
        elif(erase_status[0] == Flash_HAL_ERROR):
            print("\n   Erase Status: Fail  Code: FLASH_HAL_ERROR")
        elif(erase_status[0] == Flash_HAL_BUSY):
            print("\n   Erase Status: Fail  Code: FLASH_HAL_BUSY")
        elif(erase_status[0] == Flash_HAL_TIMEOUT):
            print("\n   Erase Status: Fail  Code: FLASH_HAL_TIMEOUT")
        elif(erase_status[0] == Flash_HAL_INV_ADDR):
            print("\n   Erase Status: Fail  Code: FLASH_HAL_INV_SECTOR")
        else:
            print("\n   Erase Status: Fail  Code: UNKNOWN_ERROR_CODE")
    else:
        print("Timeout: Bootloader is not responding")
def process_COMMAND_BL_GET_VER(length):
    ver=read_serial_port(1)
    value = bytearray(ver)
    print("\n   Bootloader Ver. : ",hex(value[0]))   
    widgets.lineEdit.setText("Current version: " +hex(value[0]))
def process_COMMAND_BL_GET_CID(length):
    value = read_serial_port(length)
    ci = (value[1] << 8 )+ value[0]
    print("\n   Chip Id. : ",hex(ci))
    widgets.lineEdit.setText("Current version: " +hex(ci))
def process_COMMAND_BL_READ_SECTOR_STATUS(length, sector):
    s_status=0

    value = read_serial_port(length)
    s_status = bytearray(value)
    #s_status.flash_sector_status = (uint16_t)(status[1] << 8 | status[0] )
    print("\n   Sector Status : ",s_status[0])
    print("\n  ====================================")
    print("\n  Sector                               \tProtection") 
    print("\n  ====================================")
    if(s_status[0] & (1 << 15)):
        #PCROP is active
        print("\n  Flash protection mode : Read/Write Protection(PCROP)\n")
    else:
        print("\n  Flash protection mode :   \tWrite Protection\n")
    for x in range(16):
        print("\n   Sector{0}                               {1}".format(x,protection_type(s_status[0],x) ) )
    widgets.lineEdit.setText("Sector {0} {1}".format(int(sector),protection_type(s_status[0],int(sector)) ))          
def process_COMMAND_BL_DIS_R_W_PROTECT(length):
    status=0
    value = read_serial_port(length)
    status = bytearray(value)
    if(status[0]):
        print("\n   FAIL")
        widgets.lineEdit.setText("Disable failed")
    else:
        print("\n   SUCCESS")
        widgets.lineEdit.setText("Disable successfully")
def process_COMMAND_BL_EN_R_W_PROTECT(length):
    status=0
    value = read_serial_port(length)
    status = bytearray(value)
    if(status[0]):
        print("\n   FAIL")
    else:
        print("\n   SUCCESS")
#-------------------------------------------------------------------------------
# Execute function
def excuteModeF4(sector):    
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    widgets.lineEdit.setText("Excute sector " +sector+" successfully")
    print("\n   Command == > BL_GO_TO_ADDR")
    
    if (sector == '0'):
        go_address = 0x08000000
    elif (sector == '1'):
        go_address = 0x08004000
    elif (sector == '2'):
        go_address = 0x08008000
    elif (sector == '3'):
        go_address = 0x0800C000
    elif (sector == '4'):
        go_address = 0x08010000 
    elif (sector == '5'):
        go_address = 0x08020000
    elif (sector == '6'):
        go_address = 0x08040000
    elif (sector == '7'):
        go_address = 0x08060000
    
    #go_address = int(address, 16)
    
    data_buf[0] = COMMAND_BL_GO_TO_ADDR_LEN-1 
    data_buf[1] = COMMAND_BL_GO_TO_ADDR 
    data_buf[2] = word_to_byte(go_address,1,1) 
    data_buf[3] = word_to_byte(go_address,2,1) 
    data_buf[4] = word_to_byte(go_address,3,1) 
    data_buf[5] = word_to_byte(go_address,4,1) 
    crc32       = get_crc(data_buf,COMMAND_BL_GO_TO_ADDR_LEN-4) 
    data_buf[6] = word_to_byte(crc32,1,1) 
    data_buf[7] = word_to_byte(crc32,2,1) 
    data_buf[8] = word_to_byte(crc32,3,1) 
    data_buf[9] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_GO_TO_ADDR_LEN]:
        Write_to_serial_port(i,COMMAND_BL_GO_TO_ADDR_LEN-1)
    
    ret_value = read_bootloader_reply(data_buf[1])
def excuteModeF1(sector):    
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    widgets.lineEdit.setText("Excute sector " +sector+" successfully")
    print("\n   Command == > BL_GO_TO_ADDR")
    

    if (sector == '0'):
        go_address = 0x08000000
    elif (sector == '1'):
        go_address = 0x08002000
    elif (sector == '2'):
        go_address = 0x08004000
    elif (sector == '3'):
        go_address = 0x08006000
    elif (sector == '4'):
        go_address = 0x08008000
    elif (sector == '5'):
        go_address = 0x0800A000
    elif (sector == '6'):
        go_address = 0x0800C000
    elif (sector == '7'):
        go_address = 0x0800E000
    elif (sector == '8'):
        go_address = 0x08010000
    elif (sector == '9'):
        go_address = 0x08012000
    elif (sector == '10'):
        go_address = 0x08014000
    elif (sector == '11'):
        go_address = 0x08016000
    elif (sector == '12'):
        go_address = 0x08018000
    elif (sector == '13'):
        go_address = 0x0801A000
    elif (sector == '14'):
        go_address = 0x0801C000
    elif (sector == '15'):
        go_address = 0x0801E000
    #go_address = int(address, 16)
    
    data_buf[0] = COMMAND_BL_GO_TO_ADDR_LEN-1 
    data_buf[1] = COMMAND_BL_GO_TO_ADDR 
    data_buf[2] = word_to_byte(go_address,1,1) 
    data_buf[3] = word_to_byte(go_address,2,1) 
    data_buf[4] = word_to_byte(go_address,3,1) 
    data_buf[5] = word_to_byte(go_address,4,1) 
    crc32       = get_crc(data_buf,COMMAND_BL_GO_TO_ADDR_LEN-4) 
    data_buf[6] = word_to_byte(crc32,1,1) 
    data_buf[7] = word_to_byte(crc32,2,1) 
    data_buf[8] = word_to_byte(crc32,3,1) 
    data_buf[9] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_GO_TO_ADDR_LEN]:
        Write_to_serial_port(i,COMMAND_BL_GO_TO_ADDR_LEN-1)
    
    ret_value = read_bootloader_reply(data_buf[1])
def excuteModeF0(sector):    
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    widgets.lineEdit.setText("Excute sector " +sector+" successfully")
    print("\n   Command == > BL_GO_TO_ADDR")
    
    #go_address = int(address, 16)
    
    if (sector == '0'):
        go_address = 0x08000000
    elif (sector == '1'):
        go_address = 0x08002000
    elif (sector == '2'):
        go_address = 0x08004000
    elif (sector == '3'):
        go_address = 0x08006000
    elif (sector == '4'):
        go_address = 0x08008000
    elif (sector == '5'):
        go_address = 0x0800A000
    elif (sector == '6'):
        go_address = 0x0800C000
    elif (sector == '7'):
        go_address = 0x0800E000
    elif (sector == '8'):
        go_address = 0x08010000
    elif (sector == '9'):
        go_address = 0x08012000
    elif (sector == '10'):
        go_address = 0x08014000
    elif (sector == '11'):
        go_address = 0x08016000
    elif (sector == '12'):
        go_address = 0x08018000
    elif (sector == '13'):
        go_address = 0x0801A000
    elif (sector == '14'):
        go_address = 0x0801C000
    elif (sector == '15'):
        go_address = 0x0801E000
        
    sector_numbers = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    sector_details = 0
    x = int(sector)
    sector_numbers[x]=int(sector.format(x+1) )
    sector_details = sector_details | (1 << sector_numbers[x])
    
    data_buf[0] = COMMAND_BL_GO_TO_ADDR_LEN-1 
    data_buf[1] = COMMAND_BL_GO_TO_ADDR 
    data_buf[2] = sector_details 
    data_buf[3] = word_to_byte(go_address,1,1) 
    data_buf[4] = word_to_byte(go_address,2,1) 
    data_buf[5] = word_to_byte(go_address,3,1) 
    data_buf[6] = word_to_byte(go_address,4,1) 
    crc32       = get_crc(data_buf,COMMAND_BL_GO_TO_ADDR_LEN-4) 
    data_buf[7] = word_to_byte(crc32,1,1) 
    data_buf[8] = word_to_byte(crc32,2,1) 
    data_buf[9] = word_to_byte(crc32,3,1) 
    data_buf[10] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_GO_TO_ADDR_LEN]:
        Write_to_serial_port(i,COMMAND_BL_GO_TO_ADDR_LEN-1)
    
    ret_value = read_bootloader_reply(data_buf[1])
def writeModeF4(path, sector):
    print("write mode f4")
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    widgets.lineEdit.setText("Write file to sector " +sector+" successfully")
    print("\n   Command == > BL_MEM_WRITE")
    bytes_remaining=0
    t_len_of_file=0
    bytes_so_far_sent = 0
    len_to_read=0
    base_mem_address=0
        
    data_buf[1] = COMMAND_BL_MEM_WRITE

    #First get the total number of bytes in the .bin file.
    t_len_of_file =calc_file_len(path)

    #keep opening the file
    open_the_file(path)

    bytes_remaining = t_len_of_file - bytes_so_far_sent
    
    if (sector == '0'):
        base_mem_address = 0x08000000
    elif (sector == '1'):
        base_mem_address = 0x08004000
    elif (sector == '2'):
        base_mem_address = 0x08008000
    elif (sector == '3'):
        base_mem_address = 0x0800C000 
    elif (sector == '4'):
        base_mem_address = 0x08010000 
    elif (sector == '5'):
        base_mem_address = 0x08020000 
    elif (sector == '6'):
        base_mem_address = 0x08040000
    elif (sector == '7'):
        base_mem_address = 0x08060000
    
    
    global mem_write_active
    while(bytes_remaining):
        mem_write_active=1
        if(bytes_remaining >= 128):
            len_to_read = 128
        else:
            len_to_read = bytes_remaining
        #get the bytes in to buffer by reading file
        for x in range(len_to_read):
            file_read_value = bin_file.read(1)
            file_read_value = bytearray(file_read_value)
            data_buf[7+x]= int(file_read_value[0])
        #read_the_file(&data_buf[7],len_to_read) 
        #print("\n   base mem address = \n",base_mem_address, hex(base_mem_address)) 

        #populate base mem address
        data_buf[2] = word_to_byte(base_mem_address,1,1)
        data_buf[3] = word_to_byte(base_mem_address,2,1)
        data_buf[4] = word_to_byte(base_mem_address,3,1)
        data_buf[5] = word_to_byte(base_mem_address,4,1)

        data_buf[6] = len_to_read

        #/* 1 byte len + 1 byte command code + 4 byte mem base address
        #* 1 byte payload len + len_to_read is amount of bytes read from file + 4 byte CRC
        #*/
        mem_write_cmd_total_len = COMMAND_BL_MEM_WRITE_LEN+len_to_read

        #first field is "len_to_follow"
        data_buf[0] =mem_write_cmd_total_len-1

        crc32       = get_crc(data_buf,mem_write_cmd_total_len-4)
        data_buf[7+len_to_read] = word_to_byte(crc32,1,1)
        data_buf[8+len_to_read] = word_to_byte(crc32,2,1)
        data_buf[9+len_to_read] = word_to_byte(crc32,3,1)
        data_buf[10+len_to_read] = word_to_byte(crc32,4,1)

        #update base mem address for the next loop
        base_mem_address+=len_to_read

        Write_to_serial_port(data_buf[0],1)
    
        for i in data_buf[1:mem_write_cmd_total_len]:
            Write_to_serial_port(i,mem_write_cmd_total_len-1)

        bytes_so_far_sent+=len_to_read
        bytes_remaining = t_len_of_file - bytes_so_far_sent
        print("\n   bytes_so_far_sent:{0} -- bytes_remaining:{1}\n".format(bytes_so_far_sent,bytes_remaining)) 
    
        ret_value = read_bootloader_reply(data_buf[1])
    mem_write_active=0
def writeModeF0(path, sector):
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    widgets.lineEdit.setText("Write file to sector " +sector+" successfully")
    print("\n   Command == > BL_MEM_WRITE")
    bytes_remaining=0
    t_len_of_file=0
    bytes_so_far_sent = 0
    len_to_read=0
    base_mem_address=0
    firstTime = True        
    data_buf[1] = COMMAND_BL_MEM_WRITE

    #First get the total number of bytes in the .bin file.
    t_len_of_file =calc_file_len(path)

    #keep opening the file
    open_the_file(path)

    bytes_remaining = t_len_of_file - bytes_so_far_sent
    
    if(sector == '0'):
        base_mem_address = 0x08000000
    elif(sector == '1'):
        base_mem_address = 0x08000001
    elif(sector == '2'):
        base_mem_address = 0x08000002
    elif(sector == '3'):
        base_mem_address = 0x08000003 
    elif(sector == '4'):
        base_mem_address = 0x08000004 
    elif(sector == '5'):
        base_mem_address = 0x08000005 
    elif(sector == '6'):
        base_mem_address = 0x08000006
    elif(sector == '7'):
        base_mem_address = 0x08000007
    elif(sector == '8'):
        base_mem_address = 0x08000008
    elif(sector == '9'):
        base_mem_address = 0x08000009
    elif(sector == '10'):
        base_mem_address = 0x0800000A
    elif(sector == '11'):
        base_mem_address = 0x0800000B
    elif(sector == '12'):
        base_mem_address = 0x0800000C
    elif(sector == '13'):
        base_mem_address = 0x0800000D
    elif(sector == '14'):
        base_mem_address = 0x0800000E
    elif(sector == '15'):
        base_mem_address = 0x0800000F
    
    
    global mem_write_active
    while(bytes_remaining):
        mem_write_active=1
        if(bytes_remaining >= 128):
            len_to_read = 128
        else:
            len_to_read = bytes_remaining
        #get the bytes in to buffer by reading file
        for x in range(len_to_read):
            file_read_value = bin_file.read(1)
            file_read_value = bytearray(file_read_value)
            data_buf[7+x]= int(file_read_value[0])
        #read_the_file(&data_buf[7],len_to_read) 
        print("\n   base mem address = \n",base_mem_address, hex(base_mem_address)) 
        if (firstTime == True):
            #populate base mem address
            data_buf[2] = word_to_byte(base_mem_address,1,1)
            data_buf[3] = word_to_byte(base_mem_address,2,1)
            data_buf[4] = word_to_byte(base_mem_address,3,1)
            data_buf[5] = word_to_byte(base_mem_address,4,1)
            firstTime = False;
        else:
            data_buf[2] = word_to_byte(0,1,1)
            data_buf[3] = word_to_byte(0,2,1)
            data_buf[4] = word_to_byte(0,3,1)
            data_buf[5] = word_to_byte(0,4,1)
        data_buf[6] = len_to_read

        #/* 1 byte len + 1 byte command code + 4 byte mem base address
        #* 1 byte payload len + len_to_read is amount of bytes read from file + 4 byte CRC
        #*/
        mem_write_cmd_total_len = COMMAND_BL_MEM_WRITE_LEN+len_to_read

        #first field is "len_to_follow"
        data_buf[0] =mem_write_cmd_total_len-1

        crc32       = get_crc(data_buf,mem_write_cmd_total_len-4)
        data_buf[7+len_to_read] = word_to_byte(crc32,1,1)
        data_buf[8+len_to_read] = word_to_byte(crc32,2,1)
        data_buf[9+len_to_read] = word_to_byte(crc32,3,1)
        data_buf[10+len_to_read] = word_to_byte(crc32,4,1)

        #update base mem address for the next loop
        base_mem_address+=len_to_read

        Write_to_serial_port(data_buf[0],1)
        #Write_to_serial_port(data_buf[0],1)
        #Write_to_serial_port(data_buf[0],1)
    
        for i in data_buf[1:mem_write_cmd_total_len]:
            Write_to_serial_port(i,mem_write_cmd_total_len-1)

        bytes_so_far_sent+=len_to_read
        bytes_remaining = t_len_of_file - bytes_so_far_sent
        print("\n   bytes_so_far_sent:{0} -- bytes_remaining:{1}\n".format(bytes_so_far_sent,bytes_remaining)) 
    
        ret_value = read_bootloader_reply(data_buf[1])
    mem_write_active=0
def writeModeF1(path, sector):
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    widgets.lineEdit.setText("Write file to sector " +sector+" successfully")
    print("\n   Command == > BL_MEM_WRITE")
    bytes_remaining=0
    t_len_of_file=0
    bytes_so_far_sent = 0
    len_to_read=0
    base_mem_address=0
        
    data_buf[1] = COMMAND_BL_MEM_WRITE

    #First get the total number of bytes in the .bin file.
    t_len_of_file =calc_file_len(path)

    #keep opening the file
    open_the_file(path)

    bytes_remaining = t_len_of_file - bytes_so_far_sent
    
    if (sector == '0'):
        base_mem_address = 0x08000000
    elif (sector == '1'):
        base_mem_address = 0x08002000
    elif (sector == '2'):
        base_mem_address = 0x08004000
    elif (sector == '3'):
        base_mem_address = 0x08006000
    elif (sector == '4'):
        base_mem_address = 0x08008000
    elif (sector == '5'):
        base_mem_address = 0x0800A000
    elif (sector == '6'):
        base_mem_address = 0x0800C000
    elif (sector == '7'):
        base_mem_address = 0x0800E000
    elif (sector == '8'):
        base_mem_address = 0x08010000
    elif (sector == '9'):
        base_mem_address = 0x08012000
    elif (sector == '10'):
        base_mem_address = 0x08014000
    elif (sector == '11'):
        base_mem_address = 0x08016000
    elif (sector == '12'):
        base_mem_address = 0x08018000
    elif (sector == '13'):
        base_mem_address = 0x0801A000
    elif (sector == '14'):
        base_mem_address = 0x0801C000
    elif (sector == '15'):
        base_mem_address = 0x0801E000
    
    
    global mem_write_active
    while(bytes_remaining):
        mem_write_active=1
        if(bytes_remaining >= 128):
            len_to_read = 128
        else:
            len_to_read = bytes_remaining
        #get the bytes in to buffer by reading file
        for x in range(len_to_read):
            file_read_value = bin_file.read(1)
            file_read_value = bytearray(file_read_value)
            data_buf[7+x]= int(file_read_value[0])
        #read_the_file(&data_buf[7],len_to_read) 
        #print("\n   base mem address = \n",base_mem_address, hex(base_mem_address)) 

        #populate base mem address
        data_buf[2] = word_to_byte(base_mem_address,1,1)
        data_buf[3] = word_to_byte(base_mem_address,2,1)
        data_buf[4] = word_to_byte(base_mem_address,3,1)
        data_buf[5] = word_to_byte(base_mem_address,4,1)

        data_buf[6] = len_to_read

        #/* 1 byte len + 1 byte command code + 4 byte mem base address
        #* 1 byte payload len + len_to_read is amount of bytes read from file + 4 byte CRC
        #*/
        mem_write_cmd_total_len = COMMAND_BL_MEM_WRITE_LEN+len_to_read

        #first field is "len_to_follow"
        data_buf[0] =mem_write_cmd_total_len-1

        crc32       = get_crc(data_buf,mem_write_cmd_total_len-4)
        data_buf[7+len_to_read] = word_to_byte(crc32,1,1)
        data_buf[8+len_to_read] = word_to_byte(crc32,2,1)
        data_buf[9+len_to_read] = word_to_byte(crc32,3,1)
        data_buf[10+len_to_read] = word_to_byte(crc32,4,1)

        #update base mem address for the next loop
        base_mem_address+=len_to_read

        Write_to_serial_port(data_buf[0],1)
    
        for i in data_buf[1:mem_write_cmd_total_len]:
            Write_to_serial_port(i,mem_write_cmd_total_len-1)

        bytes_so_far_sent+=len_to_read
        bytes_remaining = t_len_of_file - bytes_so_far_sent
        print("\n   bytes_so_far_sent:{0} -- bytes_remaining:{1}\n".format(bytes_so_far_sent,bytes_remaining)) 
    
        ret_value = read_bootloader_reply(data_buf[1])
    mem_write_active=0       
def eraseModeF4(sector, numberOfSector):
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    print("\n   Command == > BL_FLASH_ERASE")
    widgets.lineEdit.setText("Erased " +numberOfSector+ " sector from sector " +sector)
    data_buf[0] = COMMAND_BL_FLASH_ERASE_LEN-1 
    data_buf[1] = COMMAND_BL_FLASH_ERASE    
    data_buf[2]= int(sector) 
    data_buf[3]= int(numberOfSector)
    crc32 = get_crc(data_buf,COMMAND_BL_FLASH_ERASE_LEN-4) 
    data_buf[4] = word_to_byte(crc32,1,1) 
    data_buf[5] = word_to_byte(crc32,2,1) 
    data_buf[6] = word_to_byte(crc32,3,1) 
    data_buf[7] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_FLASH_ERASE_LEN]:
        Write_to_serial_port(i,COMMAND_BL_FLASH_ERASE_LEN-1)
    
    ret_value = read_bootloader_reply(data_buf[1])
def eraseModeF1(sector, numberOfSector):
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    print("\n   Command == > BL_FLASH_ERASE")
    widgets.lineEdit.setText("Erase " +numberOfSector+ " sector from sector " +sector)
    data_buf[0] = COMMAND_BL_FLASH_ERASE_LEN-1 
    data_buf[1] = COMMAND_BL_FLASH_ERASE    
    data_buf[2]= int(sector) 
    data_buf[3]= int(numberOfSector)
    crc32 = get_crc(data_buf,COMMAND_BL_FLASH_ERASE_LEN-4) 
    data_buf[4] = word_to_byte(crc32,1,1) 
    data_buf[5] = word_to_byte(crc32,2,1) 
    data_buf[6] = word_to_byte(crc32,3,1) 
    data_buf[7] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_FLASH_ERASE_LEN]:
        Write_to_serial_port(i,COMMAND_BL_FLASH_ERASE_LEN-1)
    
    ret_value = read_bootloader_reply(data_buf[1])    
def eraseModeF0(sector, numberOfSector):
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    print("\n   Command == > BL_FLASH_ERASE")
    widgets.lineEdit.setText("Erase " +numberOfSector+ " sector from sector " +sector)
    data_buf[0] = COMMAND_BL_FLASH_ERASE_LEN-1 
    data_buf[1] = COMMAND_BL_FLASH_ERASE    
    data_buf[2]= int(sector) 
    data_buf[3]= int(numberOfSector)
    crc32 = get_crc(data_buf,COMMAND_BL_FLASH_ERASE_LEN-4) 
    data_buf[4] = word_to_byte(crc32,1,1) 
    data_buf[5] = word_to_byte(crc32,2,1) 
    data_buf[6] = word_to_byte(crc32,3,1) 
    data_buf[7] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_FLASH_ERASE_LEN]:
        Write_to_serial_port(i,COMMAND_BL_FLASH_ERASE_LEN-1)
    
    ret_value = read_bootloader_reply(data_buf[1])    
def getVersionMode():
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    print("\n   Command == > BL_GET_VER")
    COMMAND_BL_GET_VER_LEN              = 6
    data_buf[0] = COMMAND_BL_GET_VER_LEN-1 
    data_buf[1] = COMMAND_BL_GET_VER 
    crc32       = get_crc(data_buf,COMMAND_BL_GET_VER_LEN-4)
    crc32 = crc32 & 0xffffffff
    data_buf[2] = word_to_byte(crc32,1,1) 
    data_buf[3] = word_to_byte(crc32,2,1) 
    data_buf[4] = word_to_byte(crc32,3,1) 
    data_buf[5] = word_to_byte(crc32,4,1) 

    
    Write_to_serial_port(data_buf[0],1)
    for i in data_buf[1:COMMAND_BL_GET_VER_LEN]:
        Write_to_serial_port(i,COMMAND_BL_GET_VER_LEN-1)
    

    ret_value = read_bootloader_reply(data_buf[1])
def getChipIDMode():
    print('Jump to get chip id mode\n')
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    print("\n   Command == > BL_GET_CID")
    COMMAND_BL_GET_CID_LEN             =6
    data_buf[0] = COMMAND_BL_GET_CID_LEN-1 
    data_buf[1] = COMMAND_BL_GET_CID 
    crc32       = get_crc(data_buf,COMMAND_BL_GET_CID_LEN-4)
    crc32 = crc32 & 0xffffffff
    data_buf[2] = word_to_byte(crc32,1,1) 
    data_buf[3] = word_to_byte(crc32,2,1) 
    data_buf[4] = word_to_byte(crc32,3,1) 
    data_buf[5] = word_to_byte(crc32,4,1) 
    Write_to_serial_port(data_buf[0],1)
    for i in data_buf[1:COMMAND_BL_GET_CID_LEN]:
        Write_to_serial_port(i,COMMAND_BL_GET_CID_LEN-1)
        

    ret_value = read_bootloader_reply(data_buf[1])
def enWriteProtectionModeF4(sector):
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    print("\n   Command == > BL_EN_R_W_PROTECT")
    sector_numbers = [0,0,0,0,0,0,0,0]
    sector_details = 0
    x = int(sector)
    sector_numbers[x]=int(sector.format(x+1) )
    sector_details = sector_details | (1 << sector_numbers[x])

    #print("Sector details",sector_details)
    
    mode = 1

    data_buf[0] = COMMAND_BL_EN_R_W_PROTECT_LEN-1 
    data_buf[1] = COMMAND_BL_EN_R_W_PROTECT 
    data_buf[2] = sector_details 
    data_buf[3] = mode 
    crc32       = get_crc(data_buf,COMMAND_BL_EN_R_W_PROTECT_LEN-4) 
    data_buf[4] = word_to_byte(crc32,1,1) 
    data_buf[5] = word_to_byte(crc32,2,1) 
    data_buf[6] = word_to_byte(crc32,3,1) 
    data_buf[7] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_EN_R_W_PROTECT_LEN]:
        Write_to_serial_port(i,COMMAND_BL_EN_R_W_PROTECT_LEN-1)
    widgets.lineEdit.setText("Enable write protection sector " +sector+ " successfully")
    ret_value = read_bootloader_reply(data_buf[1])
def enWriteProtectionModeF0F1(sector):
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    print("\n   Command == > BL_EN_R_W_PROTECT")
    sector_numbers = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    sector_details = 0
    x = int(sector)
    sector_numbers[x]=int(sector.format(x+1))
    sector_details = sector_details | (1 << sector_numbers[x])

    #print("Sector details",sector_details)
    
    mode = 1

    data_buf[0] = COMMAND_BL_EN_R_W_PROTECT_LEN-1 
    data_buf[1] = COMMAND_BL_EN_R_W_PROTECT 
    data_buf[2] = sector_details 
    data_buf[3] = mode 
    crc32       = get_crc(data_buf,COMMAND_BL_EN_R_W_PROTECT_LEN-4) 
    data_buf[4] = word_to_byte(crc32,1,1) 
    data_buf[5] = word_to_byte(crc32,2,1) 
    data_buf[6] = word_to_byte(crc32,3,1) 
    data_buf[7] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_EN_R_W_PROTECT_LEN]:
        Write_to_serial_port(i,COMMAND_BL_EN_R_W_PROTECT_LEN-1)
    widgets.lineEdit.setText("Enable write protection sector " +sector+ " successfully")
    ret_value = read_bootloader_reply(data_buf[1])
def disWriteProtectionMode():
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    print("\n   Command == > COMMAND_BL_DIS_R_W_PROTECT")
    data_buf[0] = COMMAND_BL_DIS_R_W_PROTECT_LEN-1 
    data_buf[1] = COMMAND_BL_DIS_R_W_PROTECT 
    crc32       = get_crc(data_buf,COMMAND_BL_DIS_R_W_PROTECT_LEN-4) 
    data_buf[2] = word_to_byte(crc32,1,1) 
    data_buf[3] = word_to_byte(crc32,2,1) 
    data_buf[4] = word_to_byte(crc32,3,1) 
    data_buf[5] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_DIS_R_W_PROTECT_LEN]:
        Write_to_serial_port(i,COMMAND_BL_DIS_R_W_PROTECT_LEN-1)
    
    ret_value = read_bootloader_reply(data_buf[1])
def protectionStatus(sector):
    ret_value = 0
    data_buf = []
    for i in range(255):
        data_buf.append(0)
    print("\n   Command == > COMMAND_BL_READ_SECTOR_P_STATUS")
    data_buf[0] = COMMAND_BL_READ_SECTOR_P_STATUS_LEN-1 
    data_buf[1] = COMMAND_BL_READ_SECTOR_P_STATUS 

    crc32       = get_crc(data_buf,COMMAND_BL_READ_SECTOR_P_STATUS_LEN-4) 
    data_buf[2] = word_to_byte(crc32,1,1) 
    data_buf[3] = word_to_byte(crc32,2,1) 
    data_buf[4] = word_to_byte(crc32,3,1) 
    data_buf[5] = word_to_byte(crc32,4,1) 

    Write_to_serial_port(data_buf[0],1)
    
    for i in data_buf[1:COMMAND_BL_READ_SECTOR_P_STATUS_LEN]:
        Write_to_serial_port(i,COMMAND_BL_READ_SECTOR_P_STATUS_LEN-1)
    
    ret_value = read_bootloader_reply(data_buf[1])
def protection_type(status,n):
    if( status & (1 << 15) ):
        #PCROP is active
        if(status & (1 << n) ):
            return protection_mode[1]
        else:
            return protection_mode[2]
    else:
        if(status & (1 << n)):
            return protection_mode[2]
        else:
            return protection_mode[0]    
def read_bootloader_reply(command_code):
    #ack=[0,0]
    len_to_follow=0 
    ret = -2 

    #read_serial_port(ack,2)
    #ack = ser.read(2)
    ack=read_serial_port(2)
    if(len(ack) ):
        a_array=bytearray(ack)
        #print("read uart:",ack) 
        if (a_array[0]== 0xA5):
            #CRC of last command was good .. received ACK and "len to follow"
            len_to_follow=a_array[1]
            print("\n   CRC : SUCCESS Len :",len_to_follow)
            #print("command_code:",hex(command_code))             
            if(command_code) == COMMAND_BL_GO_TO_ADDR:
                process_COMMAND_BL_GO_TO_ADDR(len_to_follow)               
            elif(command_code) == COMMAND_BL_MEM_WRITE:
                process_COMMAND_BL_MEM_WRITE(len_to_follow)
            elif(command_code) == COMMAND_BL_FLASH_ERASE:
                process_COMMAND_BL_FLASH_ERASE(len_to_follow)
            elif (command_code) == COMMAND_BL_GET_VER :
                process_COMMAND_BL_GET_VER(len_to_follow)
            elif(command_code) == COMMAND_BL_GET_CID:
                process_COMMAND_BL_GET_CID(len_to_follow)
            elif(command_code) == COMMAND_BL_READ_SECTOR_P_STATUS:
                process_COMMAND_BL_READ_SECTOR_STATUS(len_to_follow, sector)
            elif(command_code) == COMMAND_BL_EN_R_W_PROTECT:
                process_COMMAND_BL_EN_R_W_PROTECT(len_to_follow)                
            elif(command_code) == COMMAND_BL_DIS_R_W_PROTECT:
                process_COMMAND_BL_DIS_R_W_PROTECT(len_to_follow)
            else:
                widgets.lineEdit.setText("Invalid command")
                print("\n   Invalid command code\n")
                
            ret = 0
         
        elif a_array[0] == 0x7F:
            #CRC of last command was bad .. received NACK
            print("\n   CRC: FAIL \n")
            ret= -1
    else:
        print("\n   Timeout : Bootloader not responding")
        
    return ret

#-------------------------------------------------------------------------------

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = "STM32UpdateFirmwareProgrammer"
        description = "STM32Programmer"
        # APPLY TEXTS
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.uiDefinitions(self)

        # QTableWidget PARAMETERS
        # ///////////////////////////////////////////////////////////////


        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////
        widgets.btn_connect.clicked.connect(self.buttonPressed)
        widgets.btn_getchip.clicked.connect(self.buttonPressed)
        widgets.btn_read.clicked.connect(self.buttonPressed)
        widgets.btn_dis.clicked.connect(self.buttonPressed)
        widgets.btn_write.clicked.connect(self.buttonPressed)
        widgets.btn_erase.clicked.connect(self.buttonPressed)
        widgets.btn_execute.clicked.connect(self.buttonPressed)
        widgets.btn_disConnect.clicked.connect(self.buttonPressed)
        widgets.btn_en.clicked.connect(self.buttonPressed)
        widgets.submit.clicked.connect(self.buttonPressed)
        widgets.openfile.clicked.connect(self.buttonPressed)
        widgets.btn_getver.clicked.connect(self.buttonPressed)
        
        
        # LEFT MENUS
        widgets.btn_connect.clicked.connect(self.buttonClick)
        widgets.btn_getchip.clicked.connect(self.buttonClick)
        widgets.btn_read.clicked.connect(self.buttonClick)
        widgets.btn_dis.clicked.connect(self.buttonClick)
        widgets.btn_write.clicked.connect(self.buttonClick)
        widgets.btn_erase.clicked.connect(self.buttonClick)
        widgets.btn_execute.clicked.connect(self.buttonClick)
        widgets.btn_disConnect.clicked.connect(self.buttonClick)
        widgets.btn_en.clicked.connect(self.buttonClick)
        widgets.submit.clicked.connect(self.buttonClick)
        widgets.openfile.clicked.connect(self.buttonClick)
        widgets.btn_getver.clicked.connect(self.buttonClick)
          
            

        # EXTRA LEFT BOX
        def openCloseLeftBox():
            UIFunctions.toggleLeftBox(self, True)
        widgets.toggleLeftBox.clicked.connect(openCloseLeftBox)
        widgets.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)

        # EXTRA RIGHT BOX
        

        # SHOW APP
        # ///////////////////////////////////////////////////////////////
        self.show()

        # SET CUSTOM THEME
        # ///////////////////////////////////////////////////////////////
        useCustomTheme = False
        themeFile = "themes\py_dracula_light.qss"

        # SET THEME AND HACKS
        if useCustomTheme:
            # LOAD AND APPLY STYLE
            UIFunctions.theme(self, themeFile, True)

            # SET HACKS
            AppFunctions.setThemeHack(self)

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////

    # BUTTONS CLICK
    # Post here your functions for clicked buttons
    # ///////////////////////////////////////////////////////////////
    def buttonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()
        # SHOW HOME PAGE
        if btnName == "btn_connect":            
            #currentState = "connect"
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW WIDGETS PAGE
        if btnName == "btn_getchip":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW NEW PAGE
        if btnName == "btn_read":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets) # SET PAGE
            UIFunctions.resetStyle(self, btnName) # RESET ANOTHERS BUTTONS SELECTED
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) # SELECT MENU
        if btnName == "btn_en":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        if btnName == "btn_dis":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        if btnName == "btn_write":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        if btnName == "btn_erase":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        if btnName == "btn_execute":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        if btnName == "btn_getver":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        if btnName == "btn_disConnect":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        

        # PRINT BTN NAME
        #print(f'Button "{btnName}" pressed!')

    # RESIZE EVENTS
    # ///////////////////////////////////////////////////////////////
    def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)

    # MOUSE CLICK EVENTS
    # ///////////////////////////////////////////////////////////////
    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        p = event.globalPosition()
        globalPos = p.toPoint()
        self.dragPos = globalPos

        # PRINT MOUSE EVENTS
        #if event.buttons() == Qt.LeftButton:
        #    print('Mouse click: LEFT CLICK')
        #if event.buttons() == Qt.RightButton:
        #    print('Mouse click: RIGHT CLICK')
            

    
    # COMMAND BOX 
    def text(self, text):
        self.lineEdit.setText(text)
    
    # BUTTON EVENTS
    def buttonPressed(self):
        global sector        
        global currentState
        device = widgets.comboBox.currentText()
        sector   = widgets.comboBox1.currentText()
        com = widgets.comboBox2.currentText()
        #com = temp[2:4]
        btn    = self.sender()
        btnName = btn.objectName()
        if (btnName == "btn_connect"):            
            currentState = "connect"
            listComPort()
        elif (btnName == "btn_getchip"):
            currentState = "getChipID"
        elif (btnName == "btn_getver"):
            currentState = "getVersion"
        elif (btnName == "btn_erase"):
            currentState = "erase"
        elif (btnName == "btn_write"):
            currentState = "write"
        elif (btnName == "btn_dis"):
            currentState = "disable"
        elif (btnName == "btn_en"):
            currentState = "enable"
        elif (btnName == "btn_execute"):
            currentState = "execute"
        elif (btnName == "btn_read"):
            currentState = "read"
        elif (btnName == "btn_disConnect"):
            Close_serial_port(com)
        if (btnName == "openfile"):
            openDialog(self)
        if (btnName == "submit"):           
            if (currentState == "connect"):                
                #com = widgets.lineEdit.text()
                portInit(com)
            elif (currentState == "getChipID"):
                getChipIDMode()
            elif (currentState == "getVersion"):
                getVersionMode()
            elif (currentState == "erase" and device == "STM32F4"):
                numberOfSector = widgets.lineEdit.text()
                eraseModeF4(sector, numberOfSector)
            elif (currentState == "erase" and device == "STM32F0"):
                numberOfSector = widgets.lineEdit.text()
                eraseModeF0(sector, numberOfSector)   
            elif (currentState == "erase" and device == "STM32F1"):
                numberOfSector = widgets.lineEdit.text()
                eraseModeF1(sector, numberOfSector)
            elif (currentState == "execute" and device == "STM32F4"):
                excuteModeF4(sector)
            elif (currentState == "execute" and device == "STM32F1"):
                excuteModeF1(sector)  
            elif (currentState == "execute" and device == "STM32F0"):
                excuteModeF0(sector)
            elif (currentState == "write" and device == "STM32F4"):
                path = widgets.lineEdit.text()
                writeModeF4(path, sector)
            elif (currentState == "write" and device == "STM32F0"):
                path = widgets.lineEdit.text()
                writeModeF0(path, sector)
            elif (currentState == "write" and device == "STM32F1"):
                path = widgets.lineEdit.text()
                writeModeF1(path, sector)
            elif (currentState == "enable" and device == "STM32F4"):
                enWriteProtectionModeF4(sector)
            elif (currentState == "enable" and (device == "STM32F0" or device == "STM32F1")):
                enWriteProtectionModeF0F1(sector)
            elif (currentState == "disable"):
                disWriteProtectionMode()
            elif (currentState == "read"):
                protectionStatus(sector) 


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    listComPort()
    sys.exit(app.exec())
