
# decide how much clean you want the picture.
# Value n means that we take median among pixels of square of size n by n.
def reduce_noise(a, n=7):
    import numpy as np
    am = np.zeros(
        (n, n) + (a.shape[0] - n + 1, a.shape[1] - n + 1) + a.shape[2:],
        dtype=a.dtype
    )
    for i in range(n):
        for j in range(n):
            am[i, j] = a[i:i + am.shape[2], j:j + am.shape[3]]
    am = np.moveaxis(am, (0, 1), (-2, -1)).reshape(*am.shape[2:], -1)
    am = np.median(am, axis=-1)
    if am.dtype != a.dtype:
        am = (am.astype(np.float64) + 10 ** -7).astype(a.dtype)
    return am


import PIL.Image, numpy as np

a = np.array(PIL.Image.open('testphoto.tif'))
a = reduce_noise(a)
PIL.Image.fromarray(a).save('noised_out.tif')
