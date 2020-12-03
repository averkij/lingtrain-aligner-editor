# metric graphs on pandas
# dmagin, start 01.11.2020, ver. 0.81

import numpy as np
from numpy import linalg as la

import pandas as pd
import networkx as nx

#------------------------------------------------#
class pdSpectr():
    '''Spectr of matrix'''
    def density(self):
        return ((self.vectors**2).T * self.values).T

    def invSpectr(self, scale=1, invSort=True, acc=1e-8):
        return pdSpectr((scale/self.values, self.vectors), invSort=invSort, acc=acc)

    def dfInverse(self, scale=1): # values of source inverse
        return (self.vectors.T / self.values) @ self.vectors * scale

    def dfValues(self, scale=1): # values of source
        return (self.vectors.T * self.values) @ self.vectors * scale
    
    def dfSpectr(self): # values and vectors in one data frame
        dfSp = self.vectors.copy()
        dfSp.loc[:, 'Layer'] = self.values # last column
        cols = dfSp.columns.tolist()
        cols = cols[-1:] + cols[:-1] # make first
        return dfSp[cols] 

    def iniEigen(self, eVals, eVectors, cols, invSort, acc):
        sort = -1 if invSort else 1
        eV, eF = eVals[:: sort], eVectors.T[:: sort]
        mask = np.nonzero(abs(eV) > acc) # без вырожденного слоя
        self.values = pd.Series(eV[mask])
        self.vectors = pd.DataFrame(data=eF[mask], columns=list(cols))
    
    def __init__(self, source, invSort=True, acc=1e-10): # invSort: inverse order of eigen vals
        if isinstance(source, pd.core.frame.DataFrame):
            eVals, eVectors = la.eigh(source.values)
            self.iniEigen(eVals, eVectors, source.columns, invSort, acc)
        elif isinstance(source, np.ndarray):
            eVals, eVectors = la.eigh(source.values)
            self.iniEigen(eVals, eVectors, None, invSort, acc)
        elif isinstance(source, tuple): #(eigenVals, eigenVectors)
            dsVals, dfVectors = pd.Series(source[0]), pd.DataFrame(source[1])
            self.iniEigen(dsVals.values, dfVectors.values.T, dfVectors.columns, invSort, acc)
        else:
            self.values = pd.Series()
            self.vectors = pd.DataFrame()


#------------------------------------------------#
class pdMatrix():
    '''Common matrix operations'''
    def m2DF(mX, els): return pd.DataFrame(data=mX, index=els, columns=els)

#     @staticmethod
    def minor(array, rows=None, cols=None):
        if rows is None and cols is None: return array
        if isinstance(array, pd.core.frame.DataFrame):
            if rows is None: return array.loc[:, cols]
            elif cols is None: return array.loc[rows, :]
            return array.loc[rows, cols]
        else: # np.array
            if rows is None: return np.delete(array, cols, 1)
            elif cols is None: return np.delete(array, rows, 0)
            return np.delete(np.delete(array, rows, 0), cols, 1)

    def edge(mX, scalar, row, col=None): # edging
        if col is None: col = row
        mResult = np.vstack((row, mX))
        cV = np.hstack((scalar, col))
        cV.shape = (len(cV), 1)
        return np.hstack((cV, mResult))

    def eZ(size): return np.ones([size, size])/size # symmetric projector, asymm for L: eZ = 1/(I + Lap/e), e = 1e-10
    
    def eL(size): return np.eye(size) - pdMatrix.eZ(size) # one-element of laplacian

    def mDistance(mX):
        size = len(mX)
        mDia = np.ones([size, size]) * np.diag(mX)
        return mDia + mDia.T - 2*mX

    def InvLap(Lap): #inverse laplacian (lap2green)
        isDf = isinstance(Lap, pd.core.frame.DataFrame) # else np.array
        pdSp = pdSpectr(Lap)
        invL = pdSp.dfInverse()
#         mZ = pdMatrix.eZ(len(Lap))
#         invL = la.inv(Lap + mZ) - mZ
        return pdMatrix.m2DF(invL, Lap.columns) if isDf else invL

    def green2res(Green): return pdMatrix.mDistance(Green)
    def green2gram(Green): return -pdMatrix.mDistance(Green)/2
    def gram2res(Gram): return -2*Gram
    def res2gram(Res): return -Res/2
    
    def lap2green(Lap): return pdMatrix.InvLap(Lap)
    def lap2adj(Lap): return np.diag(np.diag(Lap)) - Lap
    def adj2lap(Adj): return np.diag(Adj.sum(0)) - Adj # sum on cols

    def lap2gram(Lap): # laplacian to gramian
        return pdMatrix.green2gram(pdMatrix.lap2green(Lap))
#         isDf = isinstance(Lap, pd.core.frame.DataFrame) # else np.array
#         mF = la.inv((Lap.values[1:, 1:]) if isDf else Lap[1:, 1:]) # fundamental matrix
#         mG = -pdMatrix.edge(pdMatrix.mDistance(mF), 0, np.diag(mF))/2
#         return pdMatrix.m2DF(mG, Lap.columns) if isDf else mG

    def connects2biAdj(lConnects): # convert list of biparts connects in df adjacency matrix
        dfCons = pd.DataFrame(lConnects, columns=['from', 'to', 'weight'])
        dfAdj = dfCons.set_index(['from', 'to']).unstack(level=0).fillna(0)['weight']
        dfAdj.index.name = ''
        dfAdj.columns.name = ''
        return dfAdj

    def dfAdj2edges(dfAdj, idCols=['from', 'to', 'weight']): # convert dfAdj matrix to dfEdges
        return dfAdj.T.stack().reset_index(name=idCols[2]).rename(columns={"level_0": idCols[0], "level_1": idCols[1]})
    
    def bi2adjBasis(bcrdsObjs, adjObjs): # bi coords and connects of objects -> to connects of basis
        bcrd = pd.DataFrame(bcrdsObjs, index=adjObjs.index) # filter crds for matrix operation
        return bcrd.T @ adjObjs @ bcrd

#------------------------------------------------#
class pdGraph():
    '''Graphs on pandas
    https://networkx.org/documentation/stable/reference/convert.html#pandas graph on pandas objects'''

    '''spectr'''
    def adjSpectr(self, invSort=True): return pdSpectr(self.adj(), invSort)

    def lapSpectr(self, invSort=True): return pdSpectr(self.laplacian(), invSort)

    '''space, coordinates, projections'''
    def bcrd(self, els, baseEls=None): # bcrds of els in basis of baseEls
        if baseEls is None: baseEls = list(set(self.elements) - set(els))
        return -(self.laplacian(baseEls, els) @ self.fundamental(els))
    
    def lapProj(self, baseEls): # 
        extEls = list(set(self.elements) - set(baseEls))
        mLap = self.laplacian(extEls, baseEls)
        return mLap.T @ self.fundamental(extEls) @ mLap

    def projection(self, els): # create subGraph as projection with the same resistance values in baseEls
        lapBase = self.laplacian(els, els) - self.lapProj(els)
        return pdGraph(pdMatrix.lap2adj(lapBase))

    def vecvec(self, vec1, vec2): # scalar product of vectors on vertices: (i, j)*(k, l)
        i, j, k, l = vec1[0], vec1[1], vec2[0], vec2[1]
        R = self.resistance()
        return (R[i][l] + R[j][k] - R[i][k] - R[j][l])/2

    '''main matrices'''
    def fundamental(self, els): return pdMatrix.m2DF(la.inv(self.laplacian(els, els)), els)

    def resistance(self, rows=None, cols=None):
        if self._res is None: self._res = pdMatrix.green2res(self.green())
        return pdMatrix.minor(self._res, rows, cols)

    def gramian(self, rows=None, cols=None):
        if self._gram is None: self._gram = pdMatrix.green2gram(self.green())
        return pdMatrix.minor(self._gram, rows, cols)
    
    def green(self, rows=None, cols=None):
        if self._grn is None: self._grn = pdMatrix.InvLap(self.laplacian())
        return pdMatrix.minor(self._grn, rows, cols)

    def laplacian(self, rows=None, cols=None):
        if self._lap is None: self._lap = pdMatrix.m2DF(nx.laplacian_matrix(self.graph).todense(), self.elements)
        return pdMatrix.minor(self._lap, rows, cols)

    def adj(self, dtype=None):
        return nx.to_pandas_adjacency(self.graph, dtype=dtype)
    
    def elNorm(self, bcrd): # norm of element on its bcrds
        return -(bcrd @ self.gramian() @ bcrd)

    '''nodes properties'''
    @property
    def sn(self): # bcrds of orth centre, == (2 - (self.resistance() * self.adj()).sum(0))/2
        return (np.eye(self.numEls) - self.gramian() @ self.laplacian()).iloc[0]
    @property
    def en(self): return 2*(1 - self.sn) # resistance degree
    @property
    def cn(self): return 1 - 2*self.sn # centrality of nodes
    @property
    def degrees(self): return self.adj().sum(0) # degrees of nodes
    @property
    def res(self): return self.resistance().sum()
    
    '''graph properties'''
    @property
    def norm(self): return self.elNorm(self.sn) # norm of orth center, square of sphere radius
    @property
    def ubnorm(self): return self.norm*self.ubfactor # unbias norm
    @property
    def qnorm(self): return 4*self.norm # square of sphere diameter
    @property
    def degr(self): return 1/self.norm # resistance degree, curvature

    @property
    def ubspar(self): return self.ubnorm*self.ubdegree # unbias sparcity, =1 in complete graph, =n/2 in trees
    @property
    def ubdens(self): return 1/self.ubspar # unbias compactness, =1 in complete graph
    @property
    def sparsity(self): return self.norm*self.degree
    @property
    def density(self): return 1/self.sparsity # compactness, =1 in complete graph

    @property
    def tNumber(self): return la.det(self.laplacian().iloc[1:, 1:]) # tree number of graph
    @property
    def degree(self): return self.degrees.sum()/self.numEls # ave degree of els
    @property
    def ubdegree(self): return self.degree*self.ubfactor # unbias degree
    @property
    def ubfactor(self): return self.numEls/(self.numEls - 1) # unbias factor
    
    @property
    def numEls(self): return len(self.graph.nodes)
    @property
    def elements(self): return list(self.graph) # ==list(self.graph.nodes)
    
    def edges(self, idCols=['from', 'to', 'weight']):
        return nx.to_pandas_edgelist(self.graph, source=idCols[0], target=idCols[1])

    def ResetParams(self):
        self._lap, self._grn, self._gram, self._res = None, None, None, None
        nx.freeze(self.graph) # prevent graph modify for consistance with above matrices
        # To “unfreeze” a graph must make a copy by creating a new graph object: self.graph = nx.Graph(self.graph)

    def __init__(self, source, idCols=['from', 'to', 'weight']):
        if isinstance(source, list): # source is list of connects. Connect may be tuple (from, to, weight) or dict {'from':, 'to':, 'weight':}
            dfEdges = pd.DataFrame(source, columns=idCols)
            self.graph = nx.from_pandas_edgelist(dfEdges, idCols[0], idCols[1], [idCols[2]])

        elif isinstance(source, dict): # source is dict of dicts.
            dfEdges = pdMatrix.dfAdj2edges(pd.DataFrame(source), idCols)
            self.graph = nx.from_pandas_edgelist(dfEdges, idCols[0], idCols[1], [idCols[2]])

        elif isinstance(source, pd.core.frame.DataFrame):
            if (source.columns[0] == idCols[0]) and (source.columns[1] == idCols[1]): # source is df of connects
                self.graph = nx.from_pandas_edgelist(source, idCols[0], idCols[1], [idCols[2]])
            else: # source is df of adjacency
                # self.graph = nx.from_pandas_adjacency(source)
                dfEdges = pdMatrix.dfAdj2edges(source, idCols)
                self.graph = nx.from_pandas_edgelist(dfEdges, idCols[0], idCols[1], [idCols[2]])

        elif isinstance(source, np.ndarray): # source is np_array of adjacency 
            self.graph = nx.from_numpy_array(source)

        else: # nx.classes.graph.Graph, nx.classes.multigraph.MultiGraph
            self.graph = source

        self.ResetParams()

    @classmethod
    def props2graph(cls, dfProp): # create graphs from properties matrix
        dfmean = dfProp.mean()
        dfVprop = (dfProp - dfmean)/dfmean # vectorization
        dfGreen = dfVprop @ dfVprop.T # green matrix == correlation matrix
        return cls(pdMatrix.lap2adj(pdMatrix.InvLap(dfGreen)))
