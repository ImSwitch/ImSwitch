import numpy as np

def simulate_propagation_fft(cgh_pattern, padding=True, pad_size = 2048):
    """Simulate propagation of CGH pattern to sample plane using FFT.
    Expects cgh_pattern to be a 2D array of complex values (SLM plane).
    if padding: pads the input to max_pad size with zeros before propagation and then crops back.
    Returns normalized intensity pattern at sample plane."""

    if padding and pad_size is not None:
        h,w = cgh_pattern.shape
        pad_y = pad_size - h
        pad_x = pad_size - w
        if pad_x < 0 or pad_y < 0:
            padding = False
        else:
            cgh_pattern = np.pad(
                cgh_pattern,
                (
                    (pad_y // 2, (pad_y + 1) // 2),
                    (pad_x // 2, (pad_x + 1) // 2)
                ),
                mode='constant'
            )
    else:
        padding = False

    field_slm = cgh_pattern
    field_sample = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(field_slm)))
    intensity_sample = np.abs(field_sample) ** 2
    intensity_sample = intensity_sample / np.max(intensity_sample)  # Normalize

    # if padding:
    #     # crop back to original size
    #     h,w = cgh_pattern.shape
    #     start_y = (h - (h - pad_y)) // 2
    #     start_x = (w - (w - pad_x)) // 2
    #     intensity_sample = intensity_sample[start_y:start_y + (h - pad_y), start_x:start_x + (w - pad_x)]

    return intensity_sample