from typing import List, Union, Set

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.sparse import dok_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial.distance import cdist


def read_component_nodes(file: str) -> np.ndarray:
    """ 
    read component node list file
    """
    df = pd.read_csv(file, header=None, index_col=None)
    return df.to_numpy().astype(int).squeeze()


def read_node_locations(file: str) -> pd.DataFrame:
    """ 
    read nodal location file
    """
    df = pd.read_csv(file, sep=',', header=None, skiprows=0, index_col=0, dtype=float)
    df.index = df.index.astype(int)
    df.index.name = 'node'
    df.columns = ['x', 'y', 'z']
    return df


def read_connectivity_file(file: str) -> np.ndarray:
    """
    read connvectivity file
    """
    df = pd.read_csv(file, sep=',', header=None, index_col=None)
    return df.to_numpy().astype(int)


class Reindexer:
    """
    reindexes a node list so that for a given node list with n unique
    identifiers, the nodes are listed as 0,..,n-1. This is convinient 
    for computations on the graph where row/col position denotes node number
    """

    def __init__(self, n1: List[int],
                 n2: List[int]):
        self.new_nodes = n1
        self.old_nodes = n2

        self.__forward = dict((zip(n1, n2)))
        self.__backward = dict((zip(n2, n1)))

    @property
    def forward(self) -> dict:
        return self.__forward

    @property
    def backward(self) -> dict:
        return self.__backward

    def _transform(self, array: Union[Set, List, np.ndarray],
                   direction: str) -> np.ndarray:
        _array = np.array(array)

        return np.array([self.__getattribute__(direction)[a]
                         for a in _array.flatten()]).reshape(_array.shape)

    def forward_transform(self, array: Union[Set, List, np.ndarray]) -> np.ndarray:
        return self._transform(array, 'forward')

    def backward_transform(self, array: Union[Set, List, np.ndarray]) -> np.ndarray:
        return self._transform(array, 'backward')

    @classmethod
    def from_node_list(cls, node_list: List[int],
                       assume_sorted=False):
        if not assume_sorted:
            node_list.sort()

        nl = list(np.arange(0, len(node_list), 1, dtype=int))
        return cls(node_list, nl)


def dok_distance(connectivity: np.ndarray,
                 locations: np.ndarray) -> dok_matrix:
    dokmat = dok_matrix((locations.shape[0], locations.shape[0]))

    for e in range(connectivity.shape[0]):
        for n1 in connectivity[e, :]:
            for n2 in connectivity[e, :]:
                if (n1, n2) in dokmat:
                    pass
                else:
                    dokmat[n1, n2] = (sum((locations[n1, :] - locations[n2, :]) ** 2.0)) ** 0.5
                    dokmat[n2, n1] = dokmat[n1, n2]

    return dokmat


class LSANodePairer:

    def __init__(self, nodes1: Union[np.ndarray, pd.DataFrame],
                 nodes2: Union[np.ndarray, pd.DataFrame],
                 locations: Union[pd.DataFrame, None]):

        if nodes1.shape[0] <= nodes2.shape[0]:
            self.nodes1 = nodes1
            self.nodes2 = nodes2
        else:
            self.nodes1 = nodes2
            self.nodes2 = nodes1

        if locations is None:
            self.locations = pd.concat([self.nodes1, self.nodes2], axis=0)
            self.nodes1 = self.nodes1.index
            self.nodes2 = self.nodes2.index
            nodes = np.unique(np.concatenate([nodes1.index.to_numpy(),
                                              nodes2.index.to_numpy()], axis=0))
        else:
            self.locations = locations
            self.reindexer = Reindexer.from_node_list(
                np.unique(locations.index.to_numpy())
            )

        self.reindexer = Reindexer.from_node_list(nodes)
        self.__distance_matrix = None

    @property
    def r_nodes1(self) -> np.ndarray:
        return self.reindexer.forward_transform(self.nodes1)

    @property
    def r_nodes2(self) -> np.ndarray:
        return self.reindexer.forward_transform(self.nodes2)

    @property
    def r_locations(self) -> pd.DataFrame:
        return pd.DataFrame(self.locations.to_numpy(),
                            index=self.reindexer.forward_transform(self.locations.index))

    def pair(self,
             num_closest=None,
             reindex=False) -> np.ndarray:

        if num_closest is None:
            paired = self._pair_full()
        else:
            paired = self._pair_sparse(num_closest)

        if reindex:
            return paired
        else:
            return self.reindexer.backward_transform(paired)

    @property
    def distance_matrix(self):
        if self.__distance_matrix is None:
            self.__distance_matrix = cdist(
                self.r_locations.loc[self.r_nodes1].to_numpy(),
                self.r_locations.loc[self.r_nodes2].to_numpy()
            )

        return self.__distance_matrix

    @classmethod
    def from_locations(cls, nodes1: pd.DataFrame,
                       nodes2: pd.DataFrame):

        return cls(nodes1, nodes2, None)

    def _pair_sparse(self, num_closest: int) -> np.ndarray:

        raise NotImplementedError('havent implmented this yet, may be neccessary for very large problems?')

    def _pair_full(self) -> np.ndarray:

        matched = linear_sum_assignment(self.distance_matrix)
        return np.array([self.r_nodes1[matched[0]],
                         self.r_nodes2[matched[1]]]).T


class TSNodePairer:
    """
    TSNodePairer

    pairs nodes based on shortest paths between two sets on a graph. 
    Suitable for hexehedral (i.e. brick) meshes

    Parameters
    ----------
    nodes1: np.ndarray[int]
        a 1 dimensional array of integers containing the nodes in the first set
    nodes2: np.ndarray[int]
        a 1 dimensional array of integers containing the nodes in the second set
    locations: pd.DataFrame
        a n x 3 dataframe where n is the number of considered nodes, and the contains the
        locations in cartesian format (x,y,z) indexed by the node number
    element_connectivity: np.ndarray[int]
        an m x k array containing the k elements on each of the m elements in
        the mesh
    """

    def __init__(self, nodes1: np.ndarray,
                 nodes2: np.ndarray,
                 locations: pd.DataFrame,
                 element_connectivity: np.ndarray):

        self.reindexer = Reindexer.from_node_list(
            np.unique(locations.index.to_numpy())
        )

        self.nodes1 = nodes1
        self.nodes2 = nodes2
        self.node_graph = None
        self.locations = locations
        self.element_connectivity = element_connectivity

    @property
    def r_nodes1(self) -> np.ndarray:
        return self.reindexer.forward_transform(self.nodes1)

    @property
    def r_nodes2(self) -> np.ndarray:
        return self.reindexer.forward_transform(self.nodes2)

    @property
    def r_locations(self) -> pd.DataFrame:
        return pd.DataFrame(self.locations.to_numpy(),
                            index=self.reindexer.forward_transform(self.locations.index))

    @property
    def r_element_connectivity(self) -> np.ndarray:
        return self.reindexer.forward_transform(self.element_connectivity)

    def build_node_graph(self) -> dok_matrix:
        self.node_graph = dok_distance(self.r_element_connectivity,
                                       self.r_locations.to_numpy())

    def pair(self,
             reindex=False) -> np.ndarray:

        if self.node_graph is None:
            self.build_node_graph()

        dist_matrix = dijkstra(self.node_graph,
                               indices=self.r_nodes1)[:, self.r_nodes2]

        paired = np.array([self.r_nodes1,
                           self.r_nodes2[dist_matrix.argmin(axis=1)]]).T

        if reindex:
            return paired
        else:
            return self.reindexer.backward_transform(paired)


class ElementToNodes:
    def __init__(self, connectivity: np.ndarray,
                 values: np.ndarray):
        raise NotImplementedError('good idea, but lienar interpolation might be easier')
        assert connectivity.shape[0] == values.shape[0], 'only configured to work with \
            values defined at every element in connectivity'

        self.connectivty = connectivity
        self.values = values
        self.nodes = np.unique(connectivity[:, 1:].flatten())
        self.elements = np.unique(connectivity[:, 0])

        self.n_reindexer = Reindexer.from_node_list(self.nodes)
        self.e_reindexer = Reindexer.from_node_list(self.elements)

    @property
    def r_nodes(self) -> np.ndarray:
        return self.n_reindexer.forward_transform(self.nodes)

    @property
    def r_elements(self) -> np.ndarray:
        return self.e_reindexer.forward_transform(self.elements)

    def get_nodal_connectivity(self):
        fconn = self.connectivty[:, 1:].flatten()[None, :]
        fconn = np.abs(fconn - self.nodes[:, None])
        fconn[fconn != 0] == 1
        fconn = fconn.astype(bool)
        conn_mat = np.all(np.reshape(fconn,
                                     [self.nodes.shape[0],
                                      self.connectivty.shape[0],
                                      self.connectivty.shape[1] - 1]),
                          axis=-1)

        print(conn_mat.shape)
        print(self.connectivty.shape)

    def extrapolate_to_nodes(self):
        pass

    def __call__(self):
        pass


def main():
    nodes1 = pd.read_csv('apdl/mechanical/inner_surface_npos.dat', header=None, index_col=0)
    nodes1.index = nodes1.index.astype(int)
    nodes2 = pd.read_csv('apdl/mechanical/outer_surface_npos.dat', header=None, index_col=0)
    nodes2.index = nodes2.index.astype(int)

    node_pair = LSANodePairer.from_locations(nodes1, nodes2)
    paired = node_pair.pair()

    print(paired)

    # conn = read_connectivity_file('elem.con')
    # values = np.array([conn[:,0],np.linspace(0,conn.shape[0]-1,conn.shape[0])]).T

    # interpolator = ElementToNodes(conn,values)
    # interpolator.get_nodal_connectivity()
    # print(interpolator.n_connectivity)

    # node_pair = LSANodePairer(nodes1,nodes2,node_loc)
    # paired = node_pair.pair(num_closest= 10)
    # print(paired)
    # np.save('paired.npy',paired)
    # node_loc.to_csv('node_locations.csv')


if __name__ == '__main__':
    main()
