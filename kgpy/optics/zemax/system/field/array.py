
from kgpy.optics.zemax import ZOSAPI
from kgpy.optics.system.field import Array as ArrayBase, Item as ItemBase

from .item import Item

__all__ = []


class Array(ArrayBase):
    
    def __init__(self, zos_arr: ZOSAPI.SystemData.IFields):
        
        self.zos_arr = zos_arr
        
        ArrayBase.__init__(self)
        
    def append(self, field: ItemBase):

        if len(self.items) < 1:
            zos_field = self.zos_arr.GetField(1)

        else:
            zos_field = self.zos_arr.AddField(0.0, 0.0, 1.0)
            
        f = Item(field.x, field.y, zos_field)
        
        f.van = field.van
        f.vdx = field.vdx
        f.vdy = field.vdy
        f.vcx = field.vcx
        f.vcy = field.vcy
        
        ArrayBase.append(self, f)
