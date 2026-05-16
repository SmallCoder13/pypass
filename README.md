<img src="bastionpass/icons/BastionPass-round-1280.png"/>

**IMPORTANT NOTE:**

The latest version of Bastion Pass changed the the name of the app from PyPass to Bastion Pass. This means that if you are using the system executable, two apps with the same logo will appear. One of them will have a bundle identifier of 'com.coryellcottage.pypass', the other will have a bundle identifier of 'com.coryellcottage.bastionpass.bastionpass'. To help you tell the two apart, a new command titled 'Get App Details' has been added. You can use this new command to get the bundle identifier of either version, and the file path where your data is stored. To move your data from PyPass to Bastion Pass, you can use the new data migration feature. Note that you will have to repeat the migration process for each user saved under PyPass. It is recommended that you delete PyPass after migrating your data to Bastion Pass, to avoid confusion

This is a cross platform password manager written in python using the [beeware suite](https://beeware.org/).

***Requirements***
<ol>
  <li>Python3</li>
  <li>Git</li>
</ol>

***Installation***\
To install Bastion Pass, you have two options:

<ol>
  <li>Install from system package</li>
  <li>Install from source code</li>
</ol>

To install from your system package, just look for it in the `bastionpass/dist` folder. If you don't find it, please open an issue with your OS and a link to a (preferably) official docker image for your OS

To install from the source code, follow these steps:

***Source code Install***\
To install Bastion Pass from the source code, run these commands:
```
git clone https://github.com/coryellcottage/bastionpass
cd bastionpass/bastionpass
python3 -m venv venv
source venv/bin/activate
```

***Running Bastion Pass***\
If you installed Bastion Pass from your system package, just search for Bastion Pass in your app manager.\
\
If you installed it from the source code, follows these steps:

Go to the directory where you downloaded the source code. \
\
There should be a `bastionpass` folder. If you see those two folders, continue. If you don't see that folder, visit the Troubleshooting section below

On Linux and Mac, first activate a virtual environment:

```
source bastionpass/venv/bin/activate # Run on Linux and Mac
source bastionpass/venv/Scripts/acitavte # Run on Windows
```

Then start Bastion Pass with the following command:

```
briefcase run
```

If you can't start Bastion Pass, after activating a virtual environment, try running Bastion Pass in dev mode:
```
briefcase dev
```

If you are updating Bastion Pass instead of doing a fresh install, you may need to pass the `-ur` flag to the run command the first time after updating:

```
briefcase run -ur
```

***Troubleshooting***

If you don't see the `bastionpass` folder, then run this command:

```
cd bastionpass
```

If Bastion Pass crashes saying the briefcase command cannot be found, go to the folder where you downloaded the source code. If you see the `bastionpass`folder, run these commands:

```
source bastionpass/venv/bin/activate
pip install briefcase
```

If you have any questions, or run into any issues while using Bastion Pass, please open an [issue](https://github.com/coryellcottage/bastion-pass/issues)