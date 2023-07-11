import rasterio
import numpy as np
import os
import glob
from astropy.stats import SigmaClip
import tkinter as tk
from tkinter import filedialog, simpledialog
import matplotlib.pyplot as plt

root = tk.Tk()
root.withdraw()  # Hide the root window

# Open the file dialog in 'directory' mode
folder_path = filedialog.askdirectory()

# Ask for sigma value
sigma_value = simpledialog.askfloat("Input", "Enter the sigma value")

# Specify the output filenames
output_filename_mean = 'output_mean.tif'
output_filename_sigma = 'output_sigma_clipped.tif'

# Get a list of all GeoTIFF files in the folder
file_list = glob.glob(os.path.join(folder_path, '*.tif'))

# Initialize a list to store the data arrays from each GeoTIFF file
data_arrays = []

for file in file_list:
    # Open each GeoTIFF file
    with rasterio.open(file) as src:
        # Read the data into a numpy array and add it to the list
        data_arrays.append(src.read())

# Stack the arrays along a new dimension (axis 0)
stacked_arrays = np.stack(data_arrays, axis=0)

# Calculate the mean along axis 0
mean_array = np.mean(stacked_arrays, axis=0)

# Perform sigma clipping
sigma_clip = SigmaClip(sigma=sigma_value)
clipped_arrays = sigma_clip(stacked_arrays, axis=0)

# Calculate the mean along axis 0 of the clipped arrays
mean_array_clipped = np.mean(clipped_arrays, axis=0)

# Get the metadata from the first GeoTIFF file
with rasterio.open(file_list[0]) as src:
    meta = src.meta

# Update the metadata to reflect the number of layers in the output file
meta.update(count=1)

# Write the mean array to a new GeoTIFF file
with rasterio.open(os.path.join(folder_path, output_filename_mean), 'w', **meta) as dst:
    dst.write(mean_array)

# Write the sigma clipped mean array to a new GeoTIFF file
with rasterio.open(os.path.join(folder_path, output_filename_sigma), 'w', **meta) as dst:
    dst.write(mean_array_clipped)

# Plot the log of the mean stack and sigma clipped rasters
fig, axs = plt.subplots(1, 2, figsize=(10, 5))
axs[0].imshow(np.log1p(mean_array[0]), cmap='turbo')
axs[0].set_title('Log of Mean Stack')
axs[1].imshow(np.log1p(mean_array_clipped[0]), cmap='turbo')
axs[1].set_title('Log of Sigma Clipped')

# Save the plot to a PDF
plt.savefig(os.path.join(folder_path, 'output_plot.pdf'))
