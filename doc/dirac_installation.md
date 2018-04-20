
# DIRAC installation

Go to the following site to get the latest instructions to install DIRAC

https://www.gridpp.ac.uk/wiki/Quick_Guide_to_Dirac

As of April 2018, these instructions worked for SL6 and SL7. It has also been
tested on CentOS 6.9.

```bash
mkdir dirac_ui
cd dirac_ui
wget -np -O dirac-install https://raw.githubusercontent.com/DIRACGrid/DIRAC/integration/Core/scripts/dirac-install.py
chmod u+x dirac-install
./dirac-install -r v6r19p10 -i 27 -g v13r0
.  bashrc 
dirac-proxy-init -x # (needs user cert password)
dirac-configure -F -S GridPP -C dips://dirac01.grid.hep.ph.ic.ac.uk:9135/Configuration/Server -I
dirac-proxy-init -g t2k.org_production -M
```
