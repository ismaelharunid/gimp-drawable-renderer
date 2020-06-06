# gimp-drawable-renderer
A couple of functions to export and import drawables between a numpy ndarray and a grimp drawable.

# Warning

I put this together quickly and found that it won't work using offsets, the boundaries between 
regions and drawables is not a syncronious.  The region offsets are really only to rememner 
where they came from and do not effect and are not relevant to the region itself.  Or at least 
that seems to be the case.   So this is a know bug, no doubt there are others.  I will fix them
one by one as I have time.

