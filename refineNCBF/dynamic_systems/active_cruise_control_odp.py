import attr
import heterocl as hcl

from refineNCBF.optimized_dp_interface.odp_dynamics import OdpDynamics


@attr.s(auto_attribs=True)
class ActiveCruiseControlOdp(OdpDynamics):
    friction_coefficients = [0, 0, 0]
    target_velocity = 0
    mass = 1650
    uMode = 'max'
    control_upper_bounds = [5000.0]
    control_lower_bounds = [-5000.0]
    dMode = 'min'

    def opt_ctrl(self, t, state, spat_deriv):
        opt_a = hcl.scalar(self.control_upper_bounds[0], "opt_a")
        in2 = hcl.scalar(0, "in2")
        in3 = hcl.scalar(0, "in3")

        with hcl.if_(spat_deriv[1] < 0):
            opt_a[0] = self.control_lower_bounds[0]

        return opt_a[0], in2[0], in3[0]

    def opt_dstb(self, t, state, spat_deriv):
        d1 = hcl.scalar(0, "d1")
        d2 = hcl.scalar(0, "d2")
        d3 = hcl.scalar(0, "d3")
        return d1[0], d2[0], d3[0]

    def dynamics(self, t, state, u_opt, d_opt):
        x1_dot = hcl.scalar(0, "x1_dot")
        x2_dot = hcl.scalar(0, "x2_dot")
        x3_dot = hcl.scalar(0, "x3_dot")

        x1_dot[0] = state[1]
        x2_dot[0] = -1 / self.mass * \
                    (
                            self.friction_coefficients[0] +
                            self.friction_coefficients[1] *
                            state[1] +
                            self.friction_coefficients[2] *
                            state[1] * state[1]
                    ) \
                    + 1 / self.mass * u_opt[0]
        x3_dot[0] = self.target_velocity - state[1]
        return x1_dot[0], x2_dot[0], x3_dot[0]
