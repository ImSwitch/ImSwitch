import pipython  # PI Python wrapper, ensure it's installed via pip (pip install pipython)

from .PositionerManager import PositionerManager

from pipython import GCSDevice, GCSError

class PIFOCManager(PositionerManager):
    """ PositionerManager for control of a PI PiFOC V-308 stage through USB communication.
    
    Manager properties:

    - ``usbdevice`` -- name of the usb through which the communication should take place

    """

    def __init__(self, positionerInfo, name, *args, **lowLevelManagers):
        if len(positionerInfo.axes) != 1:
            raise RuntimeError(f'{self.__class__.__name__} only supports one axis,'
                               f' {len(positionerInfo.axes)} provided.')

        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        
        # Initialisation de la connexion USB avec le stage PI
        self._controller = GCSDevice()

        try:
            self._controller.OpenUSBDaisyChain(description=positionerInfo.managerProperties['usbdevice'])

            # Vérification de la communication avec le dispositif
            if not self._controller.IsConnected():
                raise RuntimeError(f"Échec de la connexion avec le dispositif USB {positionerInfo.managerProperties['usbdevice']}.")

            # Identification du dispositif pour s'assurer que la connexion est correcte
            device_id = self._controller.qIDN()
            print(f"Connexion établie avec succès avec le dispositif: {device_id}")

            # Initialisation du stage (vous pouvez ajouter plus de configurations si nécessaire)
            #self._controller.SVO(positionerInfo.axes, True)  # Activer la boucle fermée

        except GCSError as e:
            raise RuntimeError(f"Erreur de communication avec le dispositif: {str(e)}")

        except Exception as e:
            raise RuntimeError(f"Une erreur est survenue lors de la tentative de connexion: {str(e)}")

    def move(self, value, _):
        if value == 0:
            return
        
        axis = self.axes[0]  # Nous assumons un seul axe
        new_position = self._position[axis] + float(value)
        self._controller.MOV(axis, new_position)

        # Met à jour la position stockée
        self._position[axis] = new_position

    def setPosition(self, value, _):
        axis = self.axes[0]
        self._controller.MOV(axis, float(value))
        self._position[axis] = float(value)

    def homing(self):
        """Effectue un retour à la position d'origine (0)."""
        axis = self.axes[0]
        self._controller.FRF(axis)  # Trouver la référence (homing)
        
        # Attendre que le processus de homing soit terminé
        self._controller.WGO(axis)  # Attendre la fin du mouvement
        self._position[axis] = 0  # Mise à jour de la position à 0 une fois terminé

    @property
    def position(self):
        return self.get_abs()

    def get_abs(self):
        axis = self.axes[0]
        reply = self._controller.qPOS(axis)
        self._position[axis] = reply[axis]
        return self._position[axis]

    def close(self):
        """Appelé pour fermer la connexion avec le contrôleur."""
        self._controller.CloseConnection()


# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
