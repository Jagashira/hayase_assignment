#include <gtk/gtk.h>
#include <stdlib.h>
#include <stdio.h>

#define gdk_pixbuf_get_pixel(pixbuf,x,y,p) \
(*(gdk_pixbuf_get_pixels ((pixbuf)) + \
 gdk_pixbuf_get_rowstride ((pixbuf)) * (y) + \
 gdk_pixbuf_get_n_channels ((pixbuf)) * (x) + (p)))

int
main (int argc, char *argv[])
{
  GdkPixbuf *pixbuf = NULL;
  GError    *error  = NULL;
  int w, h, x, y;
  int r, g, b, gray;
  int n_channels;

  if (argc < 3)
    {
      g_print("Usage: %s input_image output.jpg\n", argv[0]);
      return 1;
    }

  gtk_init(&argc, &argv);

  pixbuf = gdk_pixbuf_new_from_file(argv[1], &error);
  if (pixbuf == NULL)
    {
      g_print("画像の読み込みに失敗しました: %s\n", error->message);
      g_error_free(error);
      return 1;
    }

  w = gdk_pixbuf_get_width(pixbuf);
  h = gdk_pixbuf_get_height(pixbuf);
  n_channels = gdk_pixbuf_get_n_channels(pixbuf);
  printf(" w = %d \n h = %d \n channels = %d\n",w,h,n_channels);
  int maxValue (int a,int b,int c){
    int max_value;
    if (a>b){
      max_value = a;
    }else if(max_value > c){
      return max_value;
    }else{
      max_value = c;
    }
    return max_value;
  }

  int minValue (int a,int b,int c){
    int min_value;
    if(a>b){
      min_value = b;
    }else if(min_value<c){
      return min_value;
    }else{
      return min_value;
    }
    return min_value;
  }

  for (y = 0; y < h; y++) {
    for (x = 0; x < w; x++) {
      r = gdk_pixbuf_get_pixel(pixbuf, x, y, 0);
      g = gdk_pixbuf_get_pixel(pixbuf, x, y, 1);
      b = gdk_pixbuf_get_pixel(pixbuf, x, y, 2);

      // gray = (r + g + b) / 3;
      // gray = 0.299 * r + 0.587 * g + 0.114 * b;
      gray = (maxValue(r,g,b) + minValue(r,g,b))/2;

      gdk_pixbuf_get_pixel(pixbuf, x, y, 0) = gray;
      gdk_pixbuf_get_pixel(pixbuf, x, y, 1) = gray;
      gdk_pixbuf_get_pixel(pixbuf, x, y, 2) = gray;

      if (n_channels == 4) {
      }
    }
  }

  if (!gdk_pixbuf_save(pixbuf, argv[2], "jpeg", &error, "quality", "100", NULL))
    {
      g_print("JPEG保存に失敗しました: %s\n", error->message);
      g_error_free(error);
      g_object_unref(pixbuf);
      return 1;
    }

  g_print("保存しました: %s\n", argv[2]);

  g_object_unref(pixbuf);
  return 0;
}