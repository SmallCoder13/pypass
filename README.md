DO NOT CLONE FROM THIS BRANCH!! IT MAY INCLUDE INCOMPLETE FEATURES! CLONE THE MAIN BRANCH INSTEAD

<img src="pypass/icons/PyPass-round-1280.png"/>

**IMPORTANT NOTE:**

The latest version of PyPass changed the bundle Identifier for pypass. This means that if you are using the system executable, two apps called 'PyPass' will appear. One of them will have a bundle identifier of 'com.example.pypass', the other will have a bundle identifier of 'com.coryellcottage.pypass'. To help you tell the two apart, a new command titled 'Get App Details' has been added. You can use this new command to get the bundle identifier of PyPass, and the file path where your data is stored. To move your data from the PyPass with a bundle identifier of 'com.example.pypass' to the PyPass with a bundle identifier of 'com.coryellcottage.pypass', you can use the new data migration feature. Note that you will have to repeat the migration process for each user saved under PyPass. It is recommended that you delete the version of PyPass with a bundle identifier of 'com.example.pypass' after migrating your data to the new version of pypass, to avoid confusion

This is a cross platform password manager written in python using the [beeware suite](https://beeware.org/).

***Requirements***
<ol>
  <li>Python3</li>
  <li>Git</li>
</ol>

***Installation***\
To install PyPass, you have two options:

<ol>
  <li>Install from system package</li>
  <li>Install from source code</li>
</ol>

To install from your system package, just look for it in the `dist` folder. If you don't find it, please open an issue with your OS and a link to a (preferably) offical docker image for your OS

To install from the source code, follow these steps:

***Source code Install***\
To install PyPass from the source code, run these commands:
```
git clone https://github.com/SmallCoder13/pypass
cd pypass/pypass
python3 -m venv venv
source venv/bin/activate
```

***Running PyPass***\
If you installed PyPass from your system package, just search for PyPass in your app manager.\
\
If you installed it from the source code, follows these steps:

Go to the directory where you downloaded the source code. \
\
There should be a `pypass` and a `pypass-server`. If you see those two folders, continue. If you do't see those two folders, visit the Troubleshooting section below

On Linux and Windows, run these commands:

```
souce pypass/venv/bin/activate (Run on Linux)
source pypass/venv/Scripts/acitavte (Run on Windows)
briefcase run
```

On Mac, run these commands:

```
source pypass/venv/bin/activate
briefcase dev
```

***Troubleshooting***

If you don't see the `pypass` and `pypass-server` folders, then run this command:

```
cd pypass
```

If PyPass crashes saying the briefcase command cannot be found, go to the folder where you downloaded the source code. If you see the `pypass` and `pypass-server` folders, run these commands:

```
source pypass/venv/bin activate
pip install briefcase
```

If you have any questions, or run into any issues while using PyPass, please open an [issue](https://github.com/SmallCoder13/pypass/issues)
