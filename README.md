<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>

<!--  *** Thanks for checking out the Best-README-Template. If you have a suggestion that would make this better, please fork the repo and create a pull request or simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again! Now go create something AMAZING! :D -->



<!-- /// d   u   b   p   i   x   e   l  ---  f   o   r   k   ////--v0.5.1 -->



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
<h3 align="center"><i>Automated version synchronization for Fusion 360 components and bodies</i></h3>
  <p align="center">
    Eliminates version drift by automatically keeping component/body names in sync with file versions. Extracts filename prefix, applies version tags to matching items, preserves version history in save comments, and exports tagged STL files with selective control.
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
    <li><a href="#how-version-tracking-works">How Version Tracking Works</a></li>
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

**The Problem:** When iterating on Fusion 360 designs, file versions advance but component/body names fall out of sync, making it hard to track which geometry corresponds to which version.

**The Solution:** This add-in automatically keeps everything synchronized. It extracts a 3-letter prefix from your filename (e.g., `dpx_widget.f3d` → `dpx_`), finds all components and bodies starting with that prefix, and renames them with the current file version + 1. It supports both underscore and dash separators (`dpx_lever` and `dpx-bracket` both match).

**Two-Button Workflow:**

The add-in adds two buttons to the Modify panel:

1. **DPX Versioning** — Retag matching components/bodies and save with version history comment
2. **DPX Version + Export** — Same as above, PLUS export selected items as STL files

**Version Preservation:**

Version numbers are preserved in three places:
- **Component/body names** — Visible `_vN` suffix in the design tree (e.g., `dpx_lever_v4`)
- **Save comments** — Each save includes a version-tagged comment in Fusion's version history (e.g., `[ v4 ] - Fixed mounting bracket - |3| dpx_`)
- **File metadata** — Fusion's internal version tracking

**Important Note:** Version comment tagging only works going forward from when you start using this add-in. It does not retroactively add version tags to existing file history. (Though if someone figures out how to do that retroactively, that would be awesome for a future update!)

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

### Basic Workflow

1. **Set up your naming convention**
   - Name your Fusion file with a 3-letter prefix + underscore: `dpx_widget.f3d`
   - Name components/bodies with the same prefix: `dpx_bracket`, `dpx-lever`, `dpx_mount_v03`
   - Both underscore and dash separators work: `dpx_` matches both `dpx_bracket` and `dpx-bracket`

2. **Choose your workflow button** in the Modify panel:
   - **DPX Versioning** — Just retag and save (no export)
   - **DPX Version + Export** — Retag, save, AND export selected items as STL files

3. **For Version + Export:** A checkbox panel appears showing all matching components/bodies
   - Check the items you want to export as STL files
   - All items get version-tagged regardless; checkboxes only control STL export
   - Click OK to proceed

4. **Version tagging happens automatically**
   - Script reads current file version (e.g., v3) and applies version v4 to all matching names
   - Example: `dpx_lever_v2` becomes `dpx_lever_v4`, `dpx_bracket` becomes `dpx_bracket_v4`

5. **Add an optional comment** (or leave blank)
   - You'll see a prompt: "Add an optional comment for this version (or leave blank)"
   - Your comment gets tagged with the version number in Fusion's save history
   - Example save comment: `[ v4 ] - Fixed mounting holes - |3| dpx_`

6. **File saves automatically** to keep the version number in sync
   - Your custom comment appears in Fusion's version history
   - File advances from v3 to v4

7. **If exporting:** Choose destination folder
   - Selected items export as STL with mesh refinement set to Medium
   - Visibility is handled automatically (tagged children get separate exports)
   - Exported files use the new version-tagged names: `dpx_lever_v4.stl`

### Example Scenario

**File:** `abc_housing.f3d` (currently version 5)

**Components/Bodies:**
- `abc_top_shell` 
- `abc_bottom_shell_v2`
- `abc-hinge` 
- `std_screw` (doesn't match prefix — ignored)

**After running DPX Versioning:**
- `abc_top_shell_v6`
- `abc_bottom_shell_v6` 
- `abc-hinge_v6`
- `std_screw` (unchanged)

**File version:** Now v6 with your custom comment in the history

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- VERSION TRACKING -->
## How Version Tracking Works

This add-in preserves version information in multiple places to help you track design evolution:

### Where Versions Are Stored

1. **Component and Body Names** (most visible)
   - Appears as `_vN` suffix in the design tree: `dpx_lever_v4`, `dpx_bracket_v6`
   - Always reflects file version + 1 after running the add-in
   - Helps identify which geometry belongs to which iteration

2. **Version History Comments** (most useful for tracking changes)
   - Each save includes a tagged comment in Fusion's built-in version history
   - Format: `[ v4 ] - Your custom note - |3| dpx_`
   - The `|3|` shows how many items were renamed
   - Access via File → Version History to see your annotated timeline

3. **File Metadata** (automatic)
   - Fusion's internal version counter advances with each save
   - This is what the add-in reads to calculate the next version number

### Version Comment Tagging: Not Retroactive

**Important:** Version comment tagging only works going forward. When you start using this add-in, it will tag all *future* saves with version information in the comments, but it cannot retroactively add version tags to saves that happened before you installed it.

This means:
- ✅ **New saves after installing:** Get version-tagged comments (`[ v8 ] - your note`)
- ❌ **Old saves before installing:** Keep their original comments (no version tags added)

*Future enhancement idea: Retroactively parse and tag historical saves. If you know how to do this with the Fusion API, contributions are welcome!*

### Clean UI Design

Earlier versions of this add-in showed verbose debug output listing every renamed item. That's been streamlined:
- You now see a clean summary: "Components: 2 Renamed, 1 Skipped" 
- Detailed debug info is still collected internally but hidden by default
- This keeps the user experience minimal and focused

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- REFLECTION -->
## Reflection

### What Works Well
- **Python + Fusion API** is excellent for this type of automation
- **Version sync workflow** eliminates manual tracking and human error
- **Checkbox export selection** gives granular control over what gets exported
- **Custom version comments** create a useful annotated timeline in version history
- **Prefix matching** is flexible (supports `_` and `-` separators) but strict enough to avoid false matches

### Known Limitations
- **Personal add-ins don't transfer with Autodesk accounts** — you need to reinstall when switching machines
- **Duplicate STL filenames possible** in complex assemblies with identically-named bodies in different components
- **Version comment tagging is not retroactive** — only works for saves after installation
- **Requires save operation** — file must be saved for version numbers to advance (by design, to keep sync)

### What Could Improve
- **Guaranteed unique export filenames** in all assemblies (append occurrence path or counter)
- **Optional dry-run mode** to preview changes without saving
- **Retroactive version tagging** for existing file history (requires deeper Fusion API investigation)
<!-- ROADMAP -->
## Roadmap

### Completed Features
- [x] Basic re-tagging of bodies based on file version + 1
- [x] Prefix filtering — only tags components/bodies matching filename prefix
- [x] Auto-save after tagging to maintain version sync
- [x] Component support (not just bodies)
- [x] Two-button workflow (tag-only vs tag+export)
- [x] STL export with visibility handling for tagged items
- [x] Custom comment prompt for version history annotations
- [x] Checkbox selection panel for export control
- [x] Support for both underscore and dash separators in names

### Planned Enhancements
- [ ] Guaranteed unique export filenames in all assemblies (append occurrence path)
- [ ] Optional dry-run / preview mode (show what would change without saving)
- [ ] Retroactive version tagging for existing file history (research needed)
- [ ] Configurable prefix length (currently fixed at 3 characters)

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
