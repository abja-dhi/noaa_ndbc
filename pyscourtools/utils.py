import numpy as np
import pandas as pd

class Point:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y

    def rotate(self, origin, angle):
        xo, yo = origin
        self.x = self.x - xo
        self.y = self.y - yo
        rad = np.deg2rad(angle)
        angle = -angle
        x_new = self.x * np.cos(rad) - self.y * np.sin(rad)
        y_new = self.x * np.sin(rad) + self.y * np.cos(rad)
        x_new = x_new + xo
        y_new = y_new + yo
        self.x = x_new
        self.y = y_new


    def to_list(self):
        return [self.x, self.y]

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

class Structure:
    def __init__(self, experiment) -> None:
        if isinstance(experiment, pd.DataFrame):
            self._from_df(experiment)
        else:
            self._from_experiment(experiment)
        
    def _from_df(self, experiment):
        self.p1 = Point(experiment.loc["Upstream-upper", "X"], experiment.loc["Upstream-upper", "Y"])
        self.p2 = Point(experiment.loc["Upstream-lower", "X"], experiment.loc["Upstream-lower", "Y"])
        self.p3 = Point(experiment.loc["Downstream-lower", "X"], experiment.loc["Downstream-lower", "Y"])
        self.p4 = Point(experiment.loc["Downstream-upper", "X"], experiment.loc["Downstream-upper", "Y"])

    def _from_experiment(self, experiment):
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
        
        p1 = Point(start_X, upper_y)
        p2 = Point(end_X, upper_y)
        p3 = Point(end_X, lower_y)
        p4 = Point(start_X, lower_y)
        
        if angle == np.nan:
            angle = 0

        origin = [1.95, -0.75]
        p1.rotate(origin, angle)
        p2.rotate(origin, angle)
        p3.rotate(origin, angle)
        p4.rotate(origin, angle)
        max_x = max([p1.x, p2.x, p3.x, p4.x])
        dx = max_x - 2
        p1.x = p1.x - dx
        p2.x = p2.x - dx
        p3.x = p3.x - dx
        p4.x = p4.x - dx
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4

    def __str__(self) -> str:
        return f"Structure coordinates: \n   P1: {str(self.p1)}\n   P2: {str(self.p2)}\n   P3: {str(self.p3)}\n   P4: {str(self.p4)}"


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
