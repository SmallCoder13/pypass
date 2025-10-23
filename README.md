This is a cross platform password manager written in python using the [beeware suite](https://beeware.org/).

***Requirements***
<ol>
  <li>Python3</li>
  <li>Git</li>
</ol>

***Installation***
To install PyPass, you have two options:

<ol>
  <li>Install from system package</li>
  <li>Install from source code</li>
</ol>

To install from your system package, just look for it in the `dist` folder. If you don't find it, please open an issue with your OS and a link to a (preferably) offical image for your OS

To install from the source code, follow these steps:

***Source code Install***
To install PyPass from the source code, run these commands
```
git clone https://github.com/SmallCoder13/pypass
cd pypass/pypass
python3 -m venv venv
source venv/bin/activate
```

***Running PyPass***
If you installed PyPass from your system package, just search for in your app manager. If you installed it from the source code, follows these steps:
On Linux and Windows, go to the directory where you downloaded the source code, and run `briefcase run` (make sure you activate the virtual envirnment first though with `source venv/bin/activate`)
On Mac, go to the directory where you downloaded the source code, and run `briefcase dev` (make sure you activate the virtual envirnment first though with `source venv/bin/activate`)

If it says that the briefcase command cannot be found, activate the virtual environment, and install it with:

`pip install briefcase`

If you have any questions, or run into any issues while using PyPass, please open an [issue](https://github.com/SmallCoder13/pypass/issues)
