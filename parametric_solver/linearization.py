import numpy as np
from scipy.integrate import simpson, trapezoid


def principal_stresses(tens: np.ndarray) -> np.ndarray:
    """
    Compute the principal stresses of a stress tensor - this is just the eigenvalue
    probelem at every integration point, so reshape the tensor appropriately,
    do the eigenvalue computation (which is symmetric) and return that result
    """
    mat = np.empty([tens.shape[0], 3, 3, tens.shape[-1]])

    # lazy mapping flattened symmetric tensor indices to
    # 3x3 tensor matrix - not sure if eigvalsh requires
    # the upper half of the matrix, but this is only assigning
    # the view of the matrix, not copying so this is a pretty cheap
    # operation
    mapping = {(0, 0): 0,
               (1, 1): 1,
               (2, 2): 2,
               (0, 1): 3,
               (1, 0): 3,
               (0, 2): 5,
               (2, 0): 5,
               (1, 2): 4,
               (2, 1): 4}

    for coord, idx in mapping.items():
        mat[:, coord[0], coord[1], :] = tens[:, idx, :]

    # we can use eigvalsh because the tensor is symmetric
    # have to do some swap axis here because numpy wants to compute the
    # values along the last axis, so swap, do eignvalsh, then swap back
    return np.linalg.eigvalsh(mat.swapaxes(1, -1)).swapaxes(-2, -1).squeeze()


def von_mises(stress: np.ndarray):
    """
    compute von-mises stresses
    """
    if stress.shape[1] == 3:
        return _von_mises_from_primary(stress)
    else:
        return _von_mises_from_full(stress)


def _von_mises_from_primary(stress: np.ndarray):
    """
    compute von-mises stress intensity from the primary criterion
    """
    return (0.5 ** 0.5) * np.sqrt(np.power(stress[:, 0, ...] - stress[:, 1, ...], 2.0) +
                                  np.power(stress[:, 1, ...] - stress[:, 2, ...], 2.0) +
                                  np.power(stress[:, 2, ...] - stress[:, 0, ...], 2.0))


def _von_mises_from_full(stress: np.ndarray):
    """
    compute von-mises stress intensity from the full (symmetric) stress criterion
    """
    return np.sqrt(0.5 * (np.power(stress[:, 0, ...] - stress[:, 1, ...], 2.0) +
                          np.power(stress[:, 1, ...] - stress[:, 2, ...], 2.0) +
                          np.power(stress[:, 2, ...] - stress[:, 0, ...], 2.0) +
                          6 * (np.power(stress[:, 3, ...], 2.0) + np.power(stress[:, 4, ...], 2.0) +
                               np.power(stress[:, 5, ...], 2.0))))


class APDLIntegrate:
    """
    Class for integrating "stress" - really any finite dimensional field
    across a thickness. 

    Parameters
    -----------
    stress: np.ndarray
        (N*m)xD numpy array containing the stress at the cartesian "locations. D is the number
        of dimensions in the field, for example they could be the components of the stress
        tensor, which is symmetric and can be represented as a length 6 vector, or they could
        be one-dimensional, for scalar valued fields such as temperature. m is the number of integration
        points, and N is the number of points in the mesh we are integrating over
    locations: np.ndarray
        (N*m)xn numpy array containing the "locations of the stress field. n is the number
        of coordiante dimensions i.e. 1,2,3
    npoints: int
        the number of integration points through the thickness to itegrate across, "m".
    """

    def __init__(self, stress: np.ndarray,
                 locations: np.ndarray,
                 npoints: int):

        if stress.shape[0] != locations.shape[0]:
            raise ValueError('cannot integrate on uneven arrays')

        self.npoints = npoints
        self.stress = stress.reshape([-1, npoints, stress.shape[1]])
        self.stress = self.stress.swapaxes(-1, -2)

        self.locations = locations.reshape([-1, npoints, locations.shape[1]])
        self.locations = self.locations.swapaxes(-1, -2)

    @property
    def xs(self):
        return np.linalg.norm(self.locations - self.x1[..., None], axis=1)

    @property
    def x1(self):
        return self.locations[:, :, 0]

    @property
    def x2(self):
        return self.locations[:, :, -1]

    @property
    def thick(self):
        return np.linalg.norm(self.x2 - self.x1, axis=1)

    def thickness_average(self) -> np.ndarray:
        """
        average value across the thickness
        """
        return self.membrane_tensor(averaged=True)

    def membrane_tensor(self, averaged=True) -> np.ndarray:
        """
        compute the membrane tensor at every point across
        the thickness, thus the integration is cumulative
        """
        lst = trapezoid(self.stress, x=self.xs[:, None, :], axis=2) / self.thick[:, None]

        if averaged:
            return lst
        else:
            return np.repeat(lst[..., None], self.stress.shape[-1], -1)

    def bending_tensor(self, averaged=True) -> np.ndarray:
        """ 
        compute the bending tensor, evaluates the integral definition according
        to ASME guidelines, and if averaged returns this value. If not averaged,
        then returns the "linear" representation, i.e. a line varying 
        between [-sigma_{bending},sigma_{bending}] with 0 occuring exactly at the midpoint
        of the through thickness line
        """

        xs = self.thick[:, None] / 2.0 - self.xs
        coeff = 6 / (np.power(self.thick[:, None], 2))
        bst = simpson(self.stress * xs[:, None, :], x=self.xs[:, None, :], axis=2)
        nbst = bst * coeff

        if averaged:
            return nbst
        else:
            return np.linspace(nbst, -nbst, self.stress.shape[-1]).swapaxes(0, 2).swapaxes(0, 1)

    def linearized_principal_stress(self, averaged=True) -> np.ndarray:
        """ 
        Compute the linearized principal stress, essentially just computes the lineraized
        stresses, and then computes the pinrciplate stresses of the linearized stresses.

        conanical data column representaiton on export from ADPL is: 
        x - 0
        y - 1
        z - 2
        xy - 3
        yz - 4
        xz - 5

        tau = [[sx s_xy s_xz]
                [s_xy sy s_yz]
                [s_xz s_yz z_z]]

        *noting that tau is symmetric
        """

        linear = self.membrane_tensor(averaged=averaged) + \
                 self.bending_tensor(averaged=averaged)

        if averaged:
            linear = linear[:, :, None]

        assert linear.shape[1] == 6, 'must specify stress tensor as 6 independent components'

        return principal_stresses(linear)

    def peak_tensor(self, averaged=True) -> np.ndarray:
        """
        computes the "peak" stress tensor, which is just leftover from the orignial stress 
        minus the membrane tensor and bending tensor
        """
        pt = self.stress - \
             self.membrane_tensor(averaged=False) - \
             self.bending_tensor(averaged=False)

        if averaged:
            return pt[..., [0, -1]]
        else:
            return pt

    def membrane_vm(self, averaged=True) -> np.ndarray:
        """
        convinience function for computing the von-mises membrane
        stresses
        """
        mt = self.membrane_tensor(averaged=False)
        vm = von_mises(mt)

        if averaged:
            return vm.mean(axis=-1)
        else:
            return vm

    def bending_vm(self, averaged=True) -> np.ndarray:
        """
        convinience function for computing the von-mises bending
        stresses
        """
        bt = self.bending_tensor(averaged=False)
        vm = von_mises(bt)

        if averaged:
            return vm[:, 0]
        else:
            return vm

    def triaxiality_factor(self, averaged=True) -> np.ndarray:
        """
        function for computing the "triaxility factor"
        """
        ps = principal_stresses(self.stress)

        num = ps.sum(axis=1)
        dem = _von_mises_from_primary(ps)
        tf = num / dem

        if averaged:
            return tf.mean(axis=-1)
        else:
            return tf

    def peak_vm(self, averaged=True) -> np.ndarray:
        """
        convinience function for computing the von-mises peak stresses
        """
        pt = self.peak_tensor(averaged=False)
        vm = von_mises(pt)

        if averaged:
            return vm[..., [0, -1]]
        else:
            return vm
