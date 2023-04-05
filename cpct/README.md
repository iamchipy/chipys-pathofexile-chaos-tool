# cpct

[![PyPI - Version](https://img.shields.io/pypi/v/cpct.svg)](https://pypi.org/project/cpct)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cpct.svg)](https://pypi.org/project/cpct)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)
- [chipy.dev](https://chipy.dev)

## Installation
**Two primary methods**

*PIP install method*
```console
pip install cpct --upgrade -t c:/chipy-scripts/
run C:/chipy-scripts/cpct/cpct.py OR C:/chipy-scripts/cpct/_START_HERE.cmd
```
*GitHub download*
```console
Download from [GitHub](https://github.com/iamchipy/chipys-pathofexile-chaos-tool) 
Unzip to a desired location
run _install_requirements.py (to install needed packages to global env)
run cpct.py OR _START_HERE.cmd
```

## Features
[![GUI](https://chipy.dev/res/ctcp_gui.png)](#)

**OAuth2 permissions** 
- The is the appropriate way to get correct permissions and access
- No need to dig out and reuse your webbrowser's sessionID token (which is against ToC)
- Can be easily revoked from your [PoE Profile](https://www.pathofexile.com/my-account/applications) at any time
**Automated itemfilter updating** 
- Works with existing items filters to modify/overlay recipe highlights
- Only affects item backgrouns so your existing border and text colors will be unaffected
- It can also update those when you enter a new zone to high items types that you have enough of
**Itemfilter color selection** 
- In app filter customization now allows you to select any color you like for each slot
- *PLANNED* Filters boarders/text/size will be customizable too
**Itemfilter mode selection** 
- Default will add it's recipe items colors to existing filter
- Disabled will no affect your filter at all
- *PLANNED* FilterBlade will edit the chaos recipe section of a filterblade filter




## Feature Requests

- Integration with FilterBlade filters (rather than just added it's own)
- Integration with Online filters (if possible)

## License
`cpct` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## DISCLAIMER:
This product isn't affiliated with or endorsed by Grinding Gear Games in any way.