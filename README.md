<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>

<!--  *** Thanks for checking out the Best-README-Template. If you have a suggestion that would make this better, please fork the repo and create a pull request or simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again! Now go create something AMAZING! :D -->



<!-- /// d   u   b   p   i   x   e   l  ---  f   o   r   k   ////--v0.5.1 -->
<!--this has additionally been modifed by @dubpixel for hardware use -->
<!--search dpxFusionVersioning.. search & replace is COMMAND OPTION F -->

<!--this is the version for sofrware only-->
<!--todo add small product image thats not in a details tag -->
<!--igure out how to get the details tag to properly render in jekyll for gihub pages.-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
***
-->
<div align="center">

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]
</div>
<!-- PROJECT LOGO -->
<div align="center">
  <a href="https://github.com/dubpixel/dpx_FusionVersioning">
    <img src="images/logo.png" alt="Logo" height="120">
  </a>
<h1 align="center">dpx_FusionVersioning</h1>
<h3 align="center"><i>keep body/component version tagging consistent in Fusion 360</i></h3>
  <p align="center">
    scrapes 3 letter prefix xxx_ from filename, matches components/bodies with that prefix, applies file-version+1 tags, and can export tagged STL files.
    <br />
     »  
     <a href="https://github.com/dubpixel/dpx_FusionVersioning"><strong>Project Here!</strong></a>
     »  
     <br />
    <a href="https://github.com/dubpixel/dpx_FusionVersioning/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/dubpixel/dpx_FusionVersioning/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
    </p>
</div>
   <br />
<!-- TABLE OF CONTENTS -->
<details>
  <summary><h3>Table of Contents</h3></summary>
<ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>    
    <li><a href="#reflection">Reflection</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
</ol>
</details>
<!-- ABOUT THE PROJECT -->
<details>
<summary><h3>About The Project</h3></summary>
a dubpixel internal add-in for Fusion 360 to manage version tagging across components and bodies.
the add-in scrapes the 3 letter prefix xxx_ from the filename and matches names that begin with that prefix (supports both underscore and dash separators). it then applies version+1 tagging based on the current file version number and autosaves to keep versions in sync.

current workflow includes two commands in the Modify panel:
1. DPX Versioning (tag + save)
2. DPX Version + Export (tag + save + export tagged STL files)
</br>

*author: // www.dubpixel.tv  - i@dubpixel.tv* 
</br>
<h3>Images</h3>

### FRONT
![FRONT][product-front]
</details>
<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With 
 
* Python
* Autodesk Fusion 360 API
<p align="right">(<a href="#readme-top">back to top</a>)</p>
<!-- GETTING STARTED -->

## Getting Started

_Clone or download this repository. Maybe check releases first if you want a frozen build._

  ### Prerequisites
  * Fusion 360 installed (default location is easiest).
  * A saved Fusion design file (required for version-aware tagging).


  ### Installation

  1. macOS: run `./install_addin.sh` from inside this repo folder.
  2. Windows: run `install_addin.bat`.
  3. Optional on macOS: `./install_addin_rsync.sh` for rsync-style copy with progress.
  *NOTE*: scripts copy this folder into the Fusion AddIns directory.

  4. Manifest is set to run on startup, but you may still need to enable the add-in once in Fusion.

  5. In Fusion: Utilities -> Add-Ins -> Scripts and Add-Ins -> Add-Ins tab.

  6. Find dpxVersioning, enable it, and set Run on Startup if desired.

  7. Open the Design workspace and check Modify panel for:
     - DPX Versioning
     - DPX Version + Export


<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

   _in fusion360_
1. Name your Fusion file with a 3 letter prefix followed by underscore.
  ex: `ZYX_filename`
2. Name components/bodies with the same prefix.
  ex: `ZYX_bracket`, `ZYX-body`, `ZYX_mount_v03`
3. Click one of the buttons in Modify:
  - DPX Versioning = retag + save
  - DPX Version + Export = retag + save + STL export
4. Script reads document version N and applies `_v(N+1)` to matching names.
5. You get a save comment prompt (optional), then the file saves to keep version sync.
6. Export mode prompts for folder, then exports tagged items as STL with visibility handling.
7. Prefix matching supports both `_` and `-` separators.
<!-- REFLECTION -->
## Reflection

* what did we learn? 
  - _python for this sort of thing is excellent_
* what do we like/hate?
  - _that personal add-ins dont transfer with my account. wtf autodesk_
* what would/could we do differently?
  - _component support is in now; next is better export naming in large assemblies._
  - _maybe have a suppress save mode / dry-run mode._
<!-- ROADMAP -->
## Roadmap

- [x] basic re-tagging of body based on version+1
- [x] screen only objects with 3 letter prefix used in filename
- [x] autosave after tagging
- [x] extend to components
- [x] add second button for version+export
- [x] export tagged components/bodies to STL
- [ ] add guaranteed unique export filenames in all assemblies
- [ ] add optional dry-run / no-save mode

See the [open issues](https://github.com/dubpixel/dpx_FusionVersioning/issues) for a full list of proposed features (and known issues).

<!-- CONTRIBUTING -->
## Contributing

_Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**._

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Top contributors:
<a href="https://github.com/dubpixel/dpx_FusionVersioning/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=dubpixel/dpx_FusionVersioning" alt="contrib.rocks image" />
</a>

<!-- LICENSE -->
## License

  Distributed under the Unlicense. See `LICENSE.txt` for more information.
<!-- CONTACT -->
## Contact

  ### Joshua Fleitell - i@dubpixel.tv

  Project Link: [https://github.com/dubpixel/dpx_FusionVersioning](https://github.com/dubpixel/dpx_FusionVersioning)

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

<!--
  * [ ]() - the best !
-->

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/dubpixel/dpx_FusionVersioning.svg?style=flat-square
[contributors-url]: https://github.com/dubpixel/dpx_FusionVersioning/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/gdubpixel/dpx_FusionVersioning.svg?style=flat-square
[forks-url]: https://github.com/dubpixel/dpx_FusionVersioning/network/members
[stars-shield]: https://img.shields.io/github/stars/dubpixel/dpx_FusionVersioning.svg?style=flat-square
[stars-url]: https://github.com/dubpixel/dpx_FusionVersioning/stargazers
[issues-shield]: https://img.shields.io/github/issues/dubpixel/dpx_FusionVersioning.svg?style=flat-square
[issues-url]: https://github.com/dubpixel/dpx_FusionVersioning/issues
[license-shield]: https://img.shields.io/github/license/dubpixel/dpx_FusionVersioning.svg?style=flat-square
[license-url]: https://github.com/dubpixel/dpx_FusionVersioning/blob/main/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/jfleitell
[product-front]: images/front.png
[product-rear]: images/rear.png
[product-front-rendering]: images/front_render.png
[product-rear-rendering]: images/rear_render.png
[product-pcbFront]: images/pcb_front.png
[product-pcbRear]: images/pcb_rear.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
[KiCad.org]: https://img.shields.io/badge/KiCad-v8.0.6-blue
[KiCad-url]: https://kicad.org 
[Fusion-360]: https://img.shields.io/badge/Fusion360-v4.2.0-green
[Autodesk-url]: https://autodesk.com 
[FastLed.io]: https://img.shields.io/badge/FastLED-v3.9.9-red
[FastLed-url]: https://fastled.io 
