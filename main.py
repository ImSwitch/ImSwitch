from imswitch.__main__ import main
#sudo usermod -a -G dialout bene
#export DISPLAY=:0
#export QT_QPA_PLATFORM=offscreen
import subprocess
subprocess.run(["export", "DISPLAY=:0"], shell=True)
subprocess.run(["export", "QT_QPA_PLATFORM=offscreen"], shell=True)

main()