import rpyc

def connect_to_server():
    # Connect to the RPyC server
    conn = rpyc.connect("localhost", 18861)
    
    # Access and call remote methods
    print("Adding 5 + 3:", conn.root.add(5, 3))
    print("Subtracting 5 - 3:", conn.root.subtract(5, 3))

    conn.root.snapImage()
    # Close the connection
    conn.close()

if __name__ == "__main__":
    connect_to_server()
