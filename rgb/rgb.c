#include <gtk/gtk.h>
#include <stdlib.h>

#define NW 1200
#define NH 1200

#define gdk_pixbuf_get_pixel(pixbuf,x,y,p) \
(*(gdk_pixbuf_get_pixels ((pixbuf)) + \
 gdk_pixbuf_get_rowstride ((pixbuf)) * (y) + \
 gdk_pixbuf_get_n_channels ((pixbuf)) * (x) + (p)))




int
main (int argc, char *argv[]) 
{
  GdkPixbuf *pixbuf = NULL;
  GError    *error  = NULL;
  int w,h,r,g,b,i,j;
  
  if (argc < 2) 
    {
      g_print ("Usage: read_image imagefile\n");
      exit (0);
    }
  gtk_init (&argc, &argv);

  pixbuf = gdk_pixbuf_new_from_file (argv[1], &error);
  w=gdk_pixbuf_get_width (pixbuf);
  h=gdk_pixbuf_get_height (pixbuf);

  for(i=0;i<h;i++){
    for(j=0;j<w;j++){
      r = gdk_pixbuf_get_pixel (pixbuf, j, i, 0);
      g = gdk_pixbuf_get_pixel (pixbuf, j, i, 1);
      b = gdk_pixbuf_get_pixel (pixbuf, j, i, 2);
      printf("%d %d %d %d %d %d\n",i,j,r,g,b,r+g+b);
    }
    printf("\n");
  }
  return 0;
}
