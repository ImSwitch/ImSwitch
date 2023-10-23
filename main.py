from imswitch.__main__ import main
#sudo usermod -a -G dialout bene
import subprocess
subprocess.run(["export", "DISPLAY=:0"], shell=True)

main()