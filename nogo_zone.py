# nogo_zone.py - Prevent toolhead from entering defined bounding boxes
import logging

class NoGoZoneManager:
    def __init__(self, printer):
        self.printer = printer
        self.zones = []
        self.orig_move = None
        # Hook into the toolhead after all modules are loaded
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

    def add_zone(self, zone):
        self.zones.append(zone)

    def handle_connect(self):
        self.toolhead = self.printer.lookup_object('toolhead')
        self.gcode = self.printer.lookup_object('gcode')
        
        # Monkey-patch the toolhead move function to intercept all moves
        self.orig_move = self.toolhead.move
        self.toolhead.move = self.guarded_move

    def guarded_move(self, newpos, speed):
        # newpos is a list containing [x, y, z, e]
        curpos = self.toolhead.get_position()
        
        # We need to allow moves if X and Y are not yet homed (e.g., during the homing sequence)
        status = self.toolhead.get_status(0)
        homed_axes = status.get('homed_axes', '')
        if 'x' not in homed_axes or 'y' not in homed_axes:
            return self.orig_move(newpos, speed)

        x0, y0 = curpos[0], curpos[1]
        x1, y1 = newpos[0], newpos[1]

        for zone in self.zones:
            if self.check_intersection(x0, y0, x1, y1, zone):
                # Throw a fatal G-code error to abort the current move/print
                raise self.gcode.error(
                    "NOGO_ZONE: Move from (X:%.3f, Y:%.3f) to (X:%.3f, Y:%.3f) "
                    "would enter or cross zone '%s'!" % 
                    (x0, y0, x1, y1, zone.name)
                )

        # Move is safe, pass it back to the original Klipper move function
        return self.orig_move(newpos, speed)

    def check_intersection(self, x0, y0, x1, y1, zone):
        """Liang-Barsky line clipping algorithm to detect if path crosses the rectangle"""
        xmin, xmax = zone.x_min, zone.x_max
        ymin, ymax = zone.y_min, zone.y_max

        dx = x1 - x0
        dy = y1 - y0

        # 1. Simple endpoint checks (Are we starting or ending inside?)
        if xmin <= x0 <= xmax and ymin <= y0 <= ymax:
            return True
        if xmin <= x1 <= xmax and ymin <= y1 <= ymax:
            return True

        if dx == 0.0 and dy == 0.0:
            return False

        # 2. Path intersection check
        t_min = 0.0
        t_max = 1.0

        if dx == 0.0:
            if x0 < xmin or x0 > xmax:
                return False
        else:
            tx1 = (xmin - x0) / dx
            tx2 = (xmax - x0) / dx
            t_min = max(t_min, min(tx1, tx2))
            t_max = min(t_max, max(tx1, tx2))

        if dy == 0.0:
            if y0 < ymin or y0 > ymax:
                return False
        else:
            ty1 = (ymin - y0) / dy
            ty2 = (ymax - y0) / dy
            t_min = max(t_min, min(ty1, ty2))
            t_max = min(t_max, max(ty1, ty2))

        # If t_min <= t_max, the line segment intersects the rectangle
        return t_min <= t_max


class NoGoZone:
    def __init__(self, config):
        printer = config.get_printer()
        
        # Parse the name (e.g. "[nogo_zone 0]" -> name = "0")
        name_parts = config.get_name().split(' ', 1)
        self.name = name_parts[1] if len(name_parts) > 1 else "default"
        
        # Load constraints
        self.x_min = config.getfloat('x_min')
        self.x_max = config.getfloat('x_max')
        self.y_min = config.getfloat('y_min')
        self.y_max = config.getfloat('y_max')
        
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            raise config.error(
                "nogo_zone %s: min coordinate must be strictly less than max coordinate" % self.name
            )

        # Create the manager only once, then register this specific zone into it
        manager = printer.lookup_object('nogo_zone_manager', None)
        if manager is None:
            manager = NoGoZoneManager(printer)
            printer.add_object('nogo_zone_manager', manager)
        
        manager.add_zone(self)

# Tell Klipper to load a new instance for every config block starting with "nogo_zone"
def load_config_prefix(config):
    return NoGoZone(config)