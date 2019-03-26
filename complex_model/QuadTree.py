## Python translation of QuadTree from Risk.Platform


class QuadTree(object):  # in decimal degrees dist from centroid to edge
    def __init__(self, latDim, longDim, minLatCentroid, minLongCentroid, baseSize):
        self.__longDim = longDim
        self.__latDim = latDim
        self.__minLong = minLongCentroid
        self.__baseSize = baseSize
        self.__minLat = minLatCentroid
        self.__baseGrid = [[Quad("b" + str(latInx) + "-" + str(longInx) + "-", True, self.__baseSize,
                                 latInx * 2 * self.__baseSize + self.__minLat,
                                 longInx * 2 * self.__baseSize + self.__minLong) for longInx in range(0, longDim)] for
                           latInx in range(0, latDim)]

    def Lookup(self, latitude, longitude):
        latInx = self.LatInx(latitude)
        longInx = self.LongInx(longitude)
        if latInx < 0 or latInx >= self.__latDim or longInx < 0 or longInx >= self.__longDim:
            return None
        return self.__baseGrid[latInx][longInx].Lookup(latitude, longitude)

    def LongInx(self, longitude):
        return int((longitude - self.__minLong + self.__baseSize) / (2 * self.__baseSize))

    def LatInx(self, latitude):
        return int((latitude - self.__minLat + self.__baseSize) / (2 * self.__baseSize))

    def Load(self, cellId, latitude, longitude, size):
        latInx = self.LatInx(latitude)
        longInx = self.LongInx(longitude)
        self.__baseGrid[latInx][longInx].Load(cellId, latitude, longitude, size)

    def PostLoadTest(self):
        return all([y.IsValid() for x in self.__baseGrid for y in self.__baseGrid[x]])


class Quad(object):
    def __init__(self, cellID, isLeaf, size, lat, lon):
        self.CellID = cellID
        self.IsLeaf = isLeaf
        self.WasLoaded = False
        self.Size = size  # dist from centroid to edge (start at 2.56 degrees)
        self.Lat = lat  # centroid latitude
        self.Long = lon  # centroid longitude
        self.Ne = None  # children if not a leaf
        self.Nw = None
        self.Se = None
        self.Sw = None

    def Divide(self):
        newSize = self.Size / 2
        self.IsLeaf = False
        self.Ne = Quad(self.CellID + "10", True, newSize, self.Lat + newSize, self.Long + newSize)
        self.Nw = Quad(self.CellID + "00", True, newSize, self.Lat + newSize, self.Long - newSize)
        self.Se = Quad(self.CellID + "11", True, newSize, self.Lat - newSize, self.Long + newSize)
        self.Sw = Quad(self.CellID + "01", True, newSize, self.Lat - newSize, self.Long - newSize)

    def Lookup(self, latitude, longitude):
        if self.IsLeaf:
            return self
        if latitude <= self.Lat and longitude <= self.Long:
            return self.Sw.Lookup(latitude, longitude)
        if latitude > self.Lat and longitude > self.Long:
            return self.Ne.Lookup(latitude, longitude)
        if latitude > self.Lat and longitude <= self.Long:
            return self.Nw.Lookup(latitude, longitude)
        return self.Se.Lookup(latitude, longitude)

    def Load(self, cellId, latitude, longitude, size):
        if abs(size - self.Size) < 0.00001:
            self.CellID = cellId
            self.WasLoaded = True
            return
        if self.IsLeaf:
            self.Divide()

        if latitude <= self.Lat and longitude <= self.Long:
            self.Sw.Load(cellId, latitude, longitude, size)
        if latitude > self.Lat and longitude > self.Long:
            self.Ne.Load(cellId, latitude, longitude, size)
        if latitude > self.Lat and longitude <= self.Long:
            self.Nw.Load(cellId, latitude, longitude, size)
        if latitude <= self.Lat and longitude > self.Long:
            self.Se.Load(cellId, latitude, longitude, size)

    def IsValid(self):
        if self.WasLoaded and self.IsLeaf:
            return True
        if self.WasLoaded and not self.IsLeaf:
            return False
        if not self.WasLoaded and self.IsLeaf:
            return True
        return self.Ne.IsValid() and self.Nw.IsValid() and self.Se.IsValid() and self.Sw.IsValid()
