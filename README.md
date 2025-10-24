<img src="pypass/icons/PyPass-round-1280.png"/>

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
