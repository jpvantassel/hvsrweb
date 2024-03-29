# HVSRweb - An Open-Source, Web-Based Application for Horizontal-to-Vertical Spectral Ratio Processing

> [Joseph P. Vantassel](https://github.com/jpvantassel/) and [Dana M. Brannon](https://github.com/dmbrannon)

## About HVSRweb

HVSRweb is an open-source, web-based application for performing
horizontal-to-vertical spectral ratio (HVSR) calculations in a convenient,
reliable, and statistically-consistent manner. HVSRweb allows the user to
upload three-component seismic records and perform the HVSR calculation in
the cloud, with no installation required. For the calculation details,
HVSRweb relies on the open-source Python package _hvsrpy_ developed by
Joseph P. Vantassel under the supervision of Professor Brady R. Cox at The
University of Texas at Austin. More information about  _hvsrpy_ can be found
on its [GitHub](https://github.com/jpvantassel/hvsrpy).

## Citation

If you use HVSRweb in your research or consulting we ask you
please cite the following:

> Vantassel, J.P., Cox, B.R., & Brannon, D.M. (2021). HVSRweb:
> An Open-Source, Web-Based Application for
> Horizontal-to-Vertical Spectral Ratio Processing. IFCEE
> 2021. https://doi.org/10.1061/9780784483428.005.

## Additional References

Background information concerning the HVSR statistics and the terminology can be
found in the following references:

> Cox, B. R., Cheng, T., Vantassel, J. P., & Manuel, L. (2020). A statistical
> representation and frequency-domain window-rejection algorithm for
> single-station HVSR measurements. Geophysical Journal International,
> 221(3), 2170–2183. https://doi.org/10.1093/gji/ggaa119

> Cheng, T., Cox, B. R., Vantassel, J. P., & Manuel, L. (2020). A statistical
> approach to account for azimuthal variability in single-station HVSR
> measurements. Geophysical Journal International, 223(2), 1040–1053.
> https://doi.org/10.1093/gji/ggaa342

## Running the Application

To run the application, you can either:

- Visit the [live website hosted by DesignSafe](https://hvsrweb.designsafe-ci.org/) (_recommended_), or
- Run locally

## Running Locally

To run locally:

1. Clone the repository using `git clone https://github.com/jpvantassel/hvsrweb.git`,
2. Make sure you have a modern version of Python installed (i.e., >3.6). If you
do not, you can find detailed instructions for doing so
[here](https://jpvantassel.github.io/python3-course/#/intro/installing_python).
3. Install the required dependencies using `pip install -r requirements.txt`.
If you are unfamiliar with `pip`, you may find
[this tutorial](https://jpvantassel.github.io/python3-course/#/intro/pip)
helpful.
4. Launch the application with `python hvsrweb.py` from inside the project
directory.
5. Access the localhost url (e.g., `localhost:8050`) using your favorite web
browser.

## Running an Earlier Version

All versions of HVSRweb are organized as releases. Previous versions of HVSRweb
must be run locally (i.e., are not hosted on a live website). To access and run
a previous version:

1. Go to the project's
[releases](https://github.com/jpvantassel/hvsrweb/releases) and download the
desired release.
2. Once downloaded, move and unzip the folder's contents in any convenient
location.
3. Follow the instructions for running locally (provided above) starting
from step 2.

### Example with Processing Method Set to Traditional

![gm](https://github.com/jpvantassel/hvsrweb/blob/main/img/hvsrweb_gm_screenshot.png?raw=true)

### Example with Processing Method Set to Azimuthal

![az](https://github.com/jpvantassel/hvsrweb/blob/main/img/hvsrweb_az_screenshot.png?raw=true)
