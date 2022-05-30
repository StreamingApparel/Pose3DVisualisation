# Pose3DVisualisation
Software to take time series pose information from data generating garments and replay it

![image](https://user-images.githubusercontent.com/65810138/170442694-11ff202b-f326-4058-85b9-398f309c7b48.png)

## Coordinate system
The pose is defined in a Right-Hand coordinate systems, with the axes orientated as shown in the following diagram

![image](https://user-images.githubusercontent.com/65810138/170736859-9ba70bbd-24bd-40a7-b382-d5cf9296cb17.png)

## Set up

   * Set up a python virtual environment with python=3.9 (may work with higher versions but I have not tried it)
   * Clone the repository to you local machine
```
$ git clone https://github.com/StreamingApparel/Pose3DVisualisation.git
```
   * To download the libraries needed for the software us pip and the requirements.txt file provided
```
pip install -r /path/to/requirements.txt
```
   * If that installs correctly you can test the program by typing
```
python QT_SA_Analyzer.py
```
   * Two panels should appear and you are ready to go 
 
![image](https://user-images.githubusercontent.com/65810138/170887594-194f1767-e5d7-438f-93d4-9c2ff2d438af.png)
