
from collections import Sequence, Sized
from numbers import Number

import numpy as np

#TODO: add PIL.Image support
from types import ModuleType

if 'gimp' in globals() and isinstance(gimp, ModuleType) and 'pdb' in gimp:
  if 'pdb' not in globals() or gimp.pdb is not pdb:
    pdb = gimp.pdb
else:
  gimp = pdb = None
  print "No gimp support.  Falling back on other libraries."
  print "This means there is also no pdb so no plugins either, only"
  print "drawable import and export are supported."


try:
  import PIL
except:
  PIL = None
  print "No PIL support."
  if gimp is None:
    raise NotSupportedError("With no gimp and no PIL there is not anything we can do.")


def sequence_to_ndarray(seq, dtype
    , width=None, height=None, bpp=None
    , sox=0, soy=0, sobpp=0
    , out=None
    , aox=0, aoy=0, aobpp=0
    ):
  if not isinstance(seq, Sequence):
    raise ValueError("invalid seq, expected a numby seq, suitable " \
        + "initializer or shape but found {:s} with a length of {:s}" \
        .format(type(seq).__name__ \
        , str(len(seq)) if isinstance(seq, Sized) else '(unsized)'))
  if isinstance(out, np.ndarray):
    if width is None: width = out.width-aox
    if height is None: height = out.height-aoy
    if bpp is None: bpp = out.bpp-aobpp
  if isinstance(seq, tuple) and 2 <= len(seq) and len(seq) <= 3 \
      and all(isinstance(c, Number) for c in seq): 
    # this is sort of non-sensical but it helps for calls from other functions
    array = np.ndarray(seq, dtype)
  elif len(seq) % (width*height*bpp) == 0 \
      and all(isinstance(c, Number) for c in seq):
    shape = (height or 1, width or 1, bpp or 1)
    array = np.asarray(seq, dtype=dtype).reshape(shape)
  elif len(seq) % height == 0 and all(len(c) == width for c in seq):
    array = np.asarray(seq, dtype=dtype)
  else:
    raise ValueError("invalid seq, expected a numby seq, suitable " \
        + "initializer or shape but found {:s} with a length of {:s}" \
        .format(type(seq).__name__ \
        , str(len(seq)) if isinstance(seq, Sized) else '(unsized)'))
  if isinstance(out, np.ndarray):
    if len(out.shape) == 3:
      out[aoy:aoy+height, aox:aox+width, aobpp:aobpp+bpp] = \
          array[soy:soy+height, sox:sox+width, sobpp:sobpp+bpp]
    else:
      out[aoy:aoy+height, aox:aox+width] = array[soy:soy+height, sox:sox+width]
  else:
    out = array
  return out


def gimpdrawable_to_ndarray(drawable
    , width=None, height=None, bpp=None
    , dox=None, doy=None, dobpp=0
    , out=None, dtype=None
    , aox=0, aoy=0, aobpp=0
    , scale=1
    ):
  if dox is None: dox = drawable.offsets[0]
  if doy is None: doy = drawable.offsets[1]
  if width is None: width = drawable.width-dox
  if height is None: height = drawable.height-doy
  if bpp is None: bpp = drawable.bpp-dobpp
  if isinstance(out, np.ndarray):
    shape, dtype = out.shape = out.dtype
  elif isinstance(out, Sequence) and len(out) > 1:
    if dtype is None: dtype = np.ubyte
    out = sequence_to_ndarray(seq, dtype, width, height, bpp, dox, doy, dobpp \
        , out, aox, aoy, aobpp)
  elif out is None:
    shape = (height,width,bpp)
    if dtype is None: dtype = np.ubyte
  else:
    raise ValueError("invalid out, expected a numby out, suitable " \
        + "initializer or shape but found {:s}" \
        .format(type(out).__name__))

  # well the out is all setup, now ime for a good fill
  if len(shape) == 2: shape = tuple(shape) + (bpp,)
  width = min(drawable.width, dox+width, aox+shape[1]) - dox
  height = min(drawable.height, dox+height, aox+shape[0]) - doy
  bpp = min(drawable.bpp, dobpp+bpp, shape[2] if len(shape) > 2 else 1) - dobpp
  print(dox, doy, width, height, bpp)
  region = drawable.get_pixel_rgn(dox, doy, width, height, False, False)
  rgnarray = np.fromstring(str(region[0:width,0:height]), dtype=np.ubyte).reshape((height, width, bpp))
  region = None
  if scale is not None and scale != 1:
    rgnarray *= scale
  if isinstance(out, np.ndarray):
    if len(out.shape) > 2:
      out[aoy:aoy+height, aox:aox+width, aobpp:aobpp+bpp] = rgnarray
    else:
      out[aoy:aoy+height, aox:aox+width] = rgnarray.reshape(width, height)
  else:
    out = rgnarray
  return out


def gimpdrawable_from_ndarray(image, array
    , width=None, height=None, bpp=None
    , aox=0, aoy=0, aobpp=0
    , out=None, dox=None, doy=None, dobpp=0
    , scale=1.0
    ):
  #TODO: add resize option for offsets and size going out of bounds
  if isinstance(array, Sequence):
    array = sequence_to_array(array, dtype, width, height, bpp, aox, aoy, aobpp)
  if out:
    if dox is None: dox = out.offsets[0]
    if doy is None: doy = out.offsets[1]
    if width is None: width = out.width-dox
    if height is None: height = out.height-doy
    if bpp is None: bpp = out.bpp-dobpp
  else:
    if dox is None: dox = 0
    if doy is None: doy = 0
    if width is None: width = array.shape[1]
    if height is None: height = array.shape[0]
    if bpp is None: bpp = array.shape[2] if len(array) > 2 else 1
  if out is None and isinstance(image, gimp.Image):
    print 'bpp', bpp
    layer_type = (None,GRAY_IMAGE, GRAYA_IMAGE, RGB_IMAGE, RGBA_IMAGE)[bpp]
    out = pdb.gimp_layer_new(image, width, height, layer_type, "from ndarray", 100, 0)
    pdb.gimp_image_insert_layer(image, out, None, 0)
    pdb.gimp_layer_set_offsets(out, dox, doy)
  elif not isinstance(out, gimp.Drawable):
    raise ValueError("invalid out, expected a Drawable or Image " \
        + "but found {:s}" \
        .format(type(out).__name__))
  if scale is not None and scale != 1:
    array *= scale
  region = out.get_pixel_rgn(dox, doy, width, height, True, True)
  if len(array.shape) == 3:
    region[0:width,0:height] = array[aoy:aoy+height,aox:aox+width,aobpp:aobpp+bpp] \
        .astype(np.byte).tostring()
  elif len(array.shape) == 2:
    region[0:width,0:height] = array[aoy:aoy+height,aox:aox+width] \
        .astype(np.byte).tostring()
  elif len(array.shape) == 1:
    if aox or width != region.w:
      raise OverflowError("bad boundaries of trying to fill from a 1dim array")
    i0 = aoy*width
    i1 = i0 + width * height
    region[0:width,0:height] = array[i0:i1].astype(np.byte).tostring()
  else:
    raise ValueError("invalid out, expected a numby out, suitable " \
        + "initializer or shape but found {:s}" \
        .format(type(out).__name__))
  out.merge_shadow()
  out.flush()
  out.update(dox,doy,width,height)
  return out

