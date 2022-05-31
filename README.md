# Pose3DVisualisation
Software, refered to as SA_Analyzer, takes time series pose and sensor information from data generating garments and replays and visualizes it

![image](https://user-images.githubusercontent.com/65810138/170442694-11ff202b-f326-4058-85b9-398f309c7b48.png)

## Set up

   * Set up your favourite python virtual environment with python=3.9 (may work with higher versions but I have not tried it)
   * Clone the repository to your local machine
```
$ git clone https://github.com/StreamingApparel/Pose3DVisualisation.git
```
   * To download the libraries needed for the software use pip and the requirements.txt file provided
```
pip install -r /path/to/requirements.txt
```
   * If that installs correctly you can test the program by typing
```
python QT_SA_Analyzer.py
```
   * Two panels should appear and you are ready to go 
 
![image](https://user-images.githubusercontent.com/65810138/170887594-194f1767-e5d7-438f-93d4-9c2ff2d438af.png)

## Load test file
Once the the SA_Analyser has started we can load a test file to check it is fully working. To do this click on the "File" item in the top left hand corner of the application. A dropdown menu will appear. Select "Load tracks...", this will open a file dialogue. Go to the Examples directory and select testset.sat. This will load a set of test data. If successful the Record Playback widget will show a set of selectable items. Choose one and hit the Play/Pause button, you should then see the 3D figure move.
To move around the 3D environment.
   * Click and hold the left mouse button when on the 3D view, this will change angle of view
   * To move away and closer use the mouse wheel

## Coordinate system
The pose is defined in a Right-Hand coordinate systems, with the axes orientated as shown in the following diagram

![image](https://user-images.githubusercontent.com/65810138/170736859-9ba70bbd-24bd-40a7-b382-d5cf9296cb17.png)

