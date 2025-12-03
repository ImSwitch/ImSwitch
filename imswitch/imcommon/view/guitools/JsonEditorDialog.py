import json
from qtpy import QtWidgets

class JsonEditorDialog(QtWidgets.QDialog):
    """
    Simple JSON editor dialog.
    
    Parameters
    ----------
    parent : QWidget
        Parent widget (for modality).
    params_dict : dict
        Dictionary to edit.
    """

    def __init__(self, parent, params_dict, title="Edit Parameters"):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setText(json.dumps(params_dict, indent=4))

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Edit parameters as JSON:"))
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_updated_params(self):
        """Return the edited dictionary, or None if invalid JSON."""
        try:
            return json.loads(self.text_edit.toPlainText())
        except json.JSONDecodeError:
            return None
    
    @classmethod
    def edit_params(cls, parent_widget, params_dict, title="Edit Parameters"):
        """
        Convenience method to open a JSON editor and return the updated dictionary.
        Returns None if canceled or JSON invalid.
        """
        dialog = cls(parent_widget,params_dict,title)
        dialog.setWindowTitle(title)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            return dialog.get_updated_params()
        return None