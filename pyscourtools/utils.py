import numpy as np

class Structure:
    def __init__(self, experiment) -> None:
        self.experiment = experiment
        structure = experiment.test_name.split("-")[0]
        if structure == "SC":
            self.full_name = "Single Column"
            self.width = 0.1
            self.length = 0.1
        elif structure == "SW":
            self.full_name = "Short Wall"
            self.width = 0.3
            self.length = 0.1
        elif structure == "LW":
            self.full_name = "Long Wall"
            self.width = 0.5
            self.length = 0.1
        self._get_corners()
    
    def _get_corners(self):
        angle = Angle(self.experiment).angle
        start_X = 1.9
        end_X = 2
        upper_y = (-1.5 + self.width) / 2
        lower_y = (-1.5 - self.width) / 2
        
        p1 = [start_X, upper_y]
        p2 = [end_X, upper_y]
        p3 = [end_X, lower_y]
        p4 = [start_X, lower_y]
        
        if angle == np.nan:
            angle = 0

        origin = [1.95, -0.75]
        p1 = self._rotate_point(p1, origin, angle)
        p2 = self._rotate_point(p2, origin, angle)
        p3 = self._rotate_point(p3, origin, angle)
        p4 = self._rotate_point(p4, origin, angle)
        max_x = max([p1[0], p2[0], p3[0], p4[0]])
        dx = max_x - 2
        p1[0] = p1[0] - dx
        p2[0] = p2[0] - dx
        p3[0] = p3[0] - dx
        p4[0] = p4[0] - dx
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        

    @staticmethod
    def _rotate_point(point, origin, angle):
        x, y = point
        xo, yo = origin
        x = x - xo
        y = y - yo
        rad = np.deg2rad(angle)
        angle = -angle
        x_new = x * np.cos(rad) - y * np.sin(rad)
        y_new = x * np.sin(rad) + y * np.cos(rad)
        x_new = x_new + xo
        y_new = y_new + yo
        return [x_new, y_new]



class Impoundment:
    def __init__(self, experiment) -> None:
        impoundment = experiment.test_name.split("-")[1]
        if impoundment == "H1":
            self.full_name = "70 cm"
            self.height = 0.7
        elif impoundment == "H2":
            self.full_name = "60 cm"
            self.height = 0.6
        elif impoundment == "H3":
            self.full_name = "50 cm"
            self.height = 0.5

class Angle:
    def __init__(self, experiment) -> None:
        angle = experiment.test_name.split("-")[2]
        if angle == "A0":
            self.full_name = "Not Applicable"
            self.angle = np.nan
        elif angle == "A1":
            self.full_name = "0 Degrees"
            self.angle = 0
        elif angle == "A2":
            self.full_name = "45 Degrees"
            self.angle = -45
        elif angle == "A3":
            self.full_name = "90 Degrees"
            self.angle = 90

class utils:
    @staticmethod
    def get_experiment_info(experiment):
        structure = Structure(experiment)
        impoundment = Impoundment(experiment)
        angle = Angle(experiment)
        return structure, impoundment, angle
