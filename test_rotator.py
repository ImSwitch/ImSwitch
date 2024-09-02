import usb.core
import usb.util

# Trouver tous les dispositifs USB
dev = usb.core.find(find_all=True)
for d in dev:
    print(f"ID Vendor: {hex(d.idVendor)}, ID Product: {hex(d.idProduct)}")