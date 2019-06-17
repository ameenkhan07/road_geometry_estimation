# Road Geometry Estimation

Crowdsourced Map Inference 

### Installation

Create a conda env (Conda specifically becuase of installation problems in GDAl module)

```{ssh}
conda create --name myenv3 python=3
conda activate  myenv3
conda install gdal
conda install xmltodict
conda install maptplotlib=2.2.3 #Import error in osrm
pip install osrm
pip install mapbox
pip install csv
```

