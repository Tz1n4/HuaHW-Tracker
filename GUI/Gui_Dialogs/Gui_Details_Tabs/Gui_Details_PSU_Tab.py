from GUI.Gui_Dialogs.Gui_Details_Tabs.Gui_Details_Base_Tab import BaseDetailsTab

class PSUTab(BaseDetailsTab):
    def __init__(self, file_paths=None, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths or []
        self.setup_columns(["ID (Слот)", "Health Status", "Running Status"])