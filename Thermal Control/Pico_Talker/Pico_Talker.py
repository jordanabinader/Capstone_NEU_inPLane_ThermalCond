import serial
from typing import List, Dict



def getValidSerialDevices():
    """Get list of valid serial devices to communicate with
    Validity is chosen based on the acceptable_usbid vids and pids

    Raises:
        BaseException: no acceptable serial ports

    Returns:
        List[serial.tools.list_ports.ListPortInfo]: List of serial ports that are valid devices to communicate with
    """
    acceptable_usbid = { #From :https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf?_gl=1*qx2n4b*_ga*ODk0NTkwNDExLjE2OTY2MDYxNjg.*_ga_22FD70LWDS*MTY5NjgwMjc0My40LjAuMTY5NjgwMjc0Ny4wLjAuMA..
        "Pico": {
            "vid": 0x2e8a, 
            "pid": 0x0003
        }
    }

    ports = serial.tools.list_ports.comports()

    # Check if any serial devices are acceptable for use
    acceptable_ports = []
    for port in ports:
        for k in acceptable_usbid.keys():
            if port.vid == acceptable_usbid[k]["vid"] and port.pid == acceptable_usbid[k]["pid"]:
                acceptable_ports.append(port)
    
    if acceptable_ports == []:
        raise BaseException("Computer has no connected serial devices with valid vid/pid")
    else:
        return acceptable_ports


def terminalChooseSerialDevice(ports: List[serial.tools.list_ports.ListPortInfo]):
    """ List the valid serial ports and get user input on which one to use for the function

    Args:
        ports (List[serial.tools.list_ports.ListPortInfo]): List of serial ports that are valid devices to communicate with
    """

    valid_input = False
    bad_inputs = 0
    num_ports = len(ports)

    while valid_input is False:
        if bad_inputs%3 == 0: # Reprint port options every third bad input to not clog up the terminal
            for i, port in enumerate(ports, 1):
                print("[Index] Device Path/COM Port | Manufacturer | Description")
                print(f"[{i}] {port.device} | {port} | {port.manufacturer} | {port.description}")
        
        dev = input(f"Select which Serial Device to use [1-{num_ports}]: ")

        try:
            if float(dev) == int(dev) and int(dev) in range(1, num_ports): #Make sure input was solely an integer and in the accpetable range
                return ports[int(dev)-1]
            else:
                print(f"Number was not acceptable, please input a whole number from 1 to {num_ports}")
                bad_inputs += 1
        except ValueError:
            print(f"Input was not acceptable, please input a whole number from 1 to {num_ports}")
            bad_inputs += 1


if __name__ == "__main__":
    terminalChooseSerialDevice(serial.tools.list_ports.comports())
            
            
