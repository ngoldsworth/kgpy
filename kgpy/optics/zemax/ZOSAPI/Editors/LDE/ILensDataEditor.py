
from kgpy.optics.zemax import ZOSAPI

__all__ = ['ILensDataEditor']


class ILensDataEditor:

    Editor = None                               # type: ZOSAPI.Editors.EditorType
    FirstColumn = None                          # type: ZOSAPI.Editors.LDE.SurfaceColumn
    LastColumn = None                           # type: ZOSAPI.Editors.LDE.SurfaceColumn
    MaxColumn = None                            # type: int
    MinColumn = None                            # type: int
    NumberOfNonSequentialSurfaces = None        # type: int
    NumberOfRows = None                         # type: int
    NumberOfSurfaces = None                     # type: int
    RowToSurfaceOffset = None                   # type: int
    StopSurface = None                          # type: int

    def AddRow(self) -> ZOSAPI.Editors.IEditorRow:
        pass

    def AddSurface(self) -> ZOSAPI.Editors.LDE.ILDERow:
        pass

    def CopySurfaces(self, fromSurfaceNumber: int, NumberOfSurfaces: int, toSurfaceNumber: int) -> int:
        pass

    def CopySurfaceFrom(self, fromEditor: ZOSAPI.Editors.LDE.ILensDataEditor, fromSurfaceNumber: int,
                        NumberOfSurfaces: int, toSurfaceNumber: int) -> int:
        pass

    def DeleteAllRows(self):
        pass

    def DeleteRowAt(self):
        pass

    def DeleteRowsAt(self):
        pass

    def FindLabel(self):
        pass

    def GetApodization(self):
        pass

    def GetFirstOrderData(self):
        pass

    def GetGlass(self):
        pass

    def GetGlobalMatrix(self):
        pass

    def GetIndex(self):
        pass

    def GetLabel(self):
        pass

    def GetPupil(self):
        pass

    def GetRowAt(self):
        pass

    def GetSag(self):
        pass

    def GetSurfaceAt(self):
        pass

    def GetTool_AddCoatingsToAllSurfaces(self):
        pass

    def HideEditor(self):
        pass

    def HideLDE(self):
        pass

    def InsertNewSurfaceAt(self):
        pass

    def InsertRowAt(self):
        pass

    def RemoveSurfaceAt(self):
        pass

    def RemoveSurfacesAt(self):
        pass

    def RunTool_AddCoatingsToAllSurfaces(self):
        pass

    def RunTool_ConvertGlobalToLocalCoordinates(self):
        pass

    def RunTool_ConvertLocalToGlobalCoordinates(self):
        pass

    def RunTool_ConvertSemiDiametersToCircularApertures(self):
        pass

    def RunTool_ConvertSemiDiametersToFloatingApertures(self):
        pass

    def RunTool_ConvertSemiDiametersToMaximumApertures(self):
        pass

    def RunTool_RemoveAllApertures(self):
        pass

    def RunTool_ReplaceVignettingWithApertures(self):
        pass

    def SetLabel(self):
        pass

    def ShowEditor(self):
        pass

    def ShowLDE(self):
        pass