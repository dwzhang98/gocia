
from gocia.data import atomNum, covalRadii
from ase.neighborlist import NeighborList
import numpy as np

def BLDA(elem1, elem2, sigma = 0.1, scale = 1):
    '''
    From BLDA based on covalent radii of two atoms.
    '''
    if type(elem1) is str:
        elem1, elem2 = atomNum[elem1], atomNum[elem2]
    covalBl = (covalRadii[elem1] + covalRadii[elem2])
    return np.random.normal(covalBl, sigma) * scale

def rand_direction():
    randVec = np.random.rand(3) - 0.5
    return randVec / np.sqrt(np.sum(randVec**2))

def is_withinPosLim(vec, xLim=None, yLim=None, zLim=None):
    if xLim is None: xLim = [-999, 999]
    if yLim is None: yLim = [-999, 999]
    if zLim is None: zLim = [-999, 999]
    condition = False
    if min(xLim) < vec[0] < max(xLim) and\
       min(yLim) < vec[1] < max(yLim) and\
       min(zLim) < vec[2] < max(zLim):
        condition = True
    return condition
       
def rand_point_3D(cell, xLim=None, yLim=None, zLim=None):
    flag = False
    while not flag:
        myRand = np.dot(np.random.rand(3), cell)
        if min(xLim) < myRand[0] < max(xLim) and\
           min(yLim) < myRand[1] < max(yLim) and\
           min(zLim) < myRand[2] < max(zLim):
           condition = is_withinPosLim(myRand, xLim, yLim, zLim)
    return myRand

def get_bondpairs(atoms, scale=1.1):
    """Get all pairs of bonding atoms

    Return all pairs of atoms which are closer than radius times the
    sum of their respective covalent radii.  The pairs are returned as
    tuples::

      (a, b, (i1, i2, i3))

    so that atoms a bonds to atom b displaced by the vector::

        _     _     _
      i c + i c + i c ,
       1 1   2 2   3 3

    where c1, c2 and c3 are the unit cell vectors and i1, i2, i3 are
    integers."""
    cutoffs = scale * covalRadii[atoms.numbers]
    nl = NeighborList(cutoffs=cutoffs, self_interaction=False)
    nl.update(atoms)
    bondpairs = []
    for a in range(len(atoms)):
        indices, offsets = nl.get_neighbors(a)
        bondpairs.extend([(a, a2, offset)
                          for a2, offset in zip(indices, offsets)])
    return bondpairs

def chk_bondlength(atoms, radTol = 0.2):
    bondpairs = get_bondpairs(atoms, 0.85)
    flag = True
    for bp in bondpairs:
        bl = atoms.get_distance(bp[0],bp[1], mic=True)
        stdbl = covalRadii[atoms.get_atomic_numbers()[bp[0]]]+\
                covalRadii[atoms.get_atomic_numbers()[bp[1]]]
        if bl < stdbl * (1 - radTol):
            flag = False
            break
        else: continue
    return flag

def get_neighbors(atoms, ind, chkList=None, scale = 0.85):
    cutoffs = scale * covalRadii[atoms.numbers]
    nl = NeighborList(
        cutoffs=cutoffs,
        self_interaction=False,
        bothways=True,  # or only half the list
        )
    nl.update(atoms)
    nl = nl.get_neighbors(ind)
    myNl = [[],[]]
    for i in range(len(nl[0])):
        if chkList is not None:
            if nl[0][i] in chkList:
                myNl[0].append(nl[0][i])
                myNl[1].append(nl[1][i])
        else:
            myNl[0].append(nl[0][i])
            myNl[1].append(nl[1][i])
    return myNl

def get_coordStatus(atoms, scale=1.25):
    """Returns an array of coordination numbers and an array of existing bonds determined by
    distance and covalent radii.  By default a bond is defined as 120% of the combined radii
    or less. This can be changed by setting 'covalent_percent' to a float representing a 
    factor to multiple by (default = 1.2).
    If 'exclude' is set to an array,  these atomic numbers with be unable to form bonds.
    This only excludes them from being counted from other atoms,  the coordination
    numbers for these atoms will still be calculated,  but will be unable to form
    bonds to other excluded atomic numbers.
    """

    # Get all the distances
    distances = np.divide(atoms.get_all_distances(mic=True), scale)
    
    # Atomic Numbers
    numbers = atoms.numbers
    # Coordination Numbers for each atom
    cnList, blList, nbList = [], [], []
    cr = np.take(covalRadii, numbers)
    # Array of indices of bonded atoms.  len(bonded[x]) == cn[x]
    indices = list(range(len(atoms)))
    for i in indices:
        neibInd = []
        bondLen = []
        for ii in indices:
            # Skip if measuring the same atom
            if i == ii:
                continue
            if (cr[i] + cr[ii]) >= distances[i,ii]:
                neibInd.append(ii)
                bondLen.append(distances[i,ii])
        # Add this atoms bonds to the bonded list
        nbList.append(neibInd)
        blList.append(bondLen)
    for i in nbList:
        cnList.append(len(i))
    return np.array(cnList), nbList, blList
