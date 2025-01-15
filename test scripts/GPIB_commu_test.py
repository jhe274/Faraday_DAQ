import pyvisa

def test_gpib_communication():
    # Initialize the VISA resource manager
    rm = pyvisa.ResourceManager()
    
    # Specify the GPIB address of the device
    gpib_address = "GPIB0::6::INSTR"
    
    try:
        # Open a connection to the device
        instrument = rm.open_resource(gpib_address)
        
        # Send an identification query
        response = instrument.query("*IDN?")
        
        # Print the response from the device
        print(f"Device Response: {response}")
        
        # Close the connection
        instrument.close()
        print("Communication test successful.")
    except Exception as e:
        print(f"Error communicating with the device: {e}")

if __name__ == "__main__":
    test_gpib_communication()
