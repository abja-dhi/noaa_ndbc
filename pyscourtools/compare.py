from .experiment import Experiment
from .plotter import Plotter, Specifications

class Compare:
    def __init__(self, tests) -> None:
        if isinstance(tests, Experiment):
            tests = [tests]
        self.tests = tests
    
    def compare_tests(self, instrument, description=True, x_description=0.78, y_description=0.7, add_scour=False, **kwargs) -> Plotter:
        if len(self.tests) == 1:
            raise ValueError("Only one test is provided. Nothing to compare!")
        plot = Plotter()
        spec = Specifications()
        linestyle = spec.get_linestyle()
        for test in self.tests:
            inst = getattr(test, instrument)
            inst.plot(fig=plot.fig, ax=plot.ax, description=False, set_prop=False, add_scour=add_scour, color=False, label=test.test_name)
        plot.set_prop(xlabel="Time [s]", ylabel=f"{inst.label} [{inst.unit}]", title=instrument, legend=True, grid=False, **kwargs)
        if description:
            test_names = [test.test_name for test in self.tests]
            plot.add_description(test_names, x_description=x_description, y_description=y_description)
        return plot
    