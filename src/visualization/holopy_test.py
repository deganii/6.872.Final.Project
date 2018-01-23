import holopy as hp
from holopy.scattering import calc_holo, Sphere

# center = (4, 4, 5)
center = (4, 4, 5)
sphere = Sphere(n = 1.59, r = .5, center = center )
medium_index = 1.33
illum_wavelen = 0.405
illum_polarization = (1,0)
detector = hp.detector_grid(shape = 100, spacing = 0.1)

holo = calc_holo(detector, sphere, medium_index, illum_wavelen, illum_polarization)
#hp.show(holo)
hp.save( 'holopy.tif', holo)
