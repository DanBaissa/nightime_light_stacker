import rasterio
import numpy as np
import os
import glob
from astropy.stats import SigmaClip
import matplotlib.pyplot as plt
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process .tif files to apply sigma clipping and calculate mean.")
    parser.add_argument("--folder-path", required=True, help="Path to the folder containing .tif files.")
    parser.add_argument("--sigma-value", type=float, required=True, help="Sigma value for sigma clipping.")
    parser.add_argument("--threshold-value", type=float, required=True, help="Threshold value to set numbers above this to NA.")
    return parser.parse_args()

def process_tif_files(folder_path, sigma_value, threshold_value):
    output_filename_mean = 'output_mean.tif'
    output_filename_sigma = 'output_sigma_clipped.tif'

    file_list = glob.glob(os.path.join(folder_path, '*.tif'))
    data_arrays = []
    reference_shape = None  # This will store the shape of the first valid array

    for file in file_list:
        with rasterio.open(file) as src:
            data = src.read().astype('float32')
            data[data > threshold_value] = np.nan

            if reference_shape is None:
                reference_shape = data.shape  # Set the reference shape based on the first array

            # Check if the current array's shape matches the reference shape
            if data.shape == reference_shape:
                data_arrays.append(data)
            else:
                print(f"Skipping array from {file} due to shape mismatch: expected {reference_shape}, got {data.shape}")

    if len(data_arrays) > 0:
        stacked_arrays = np.stack(data_arrays, axis=0)
        mean_array = np.nanmean(stacked_arrays, axis=0)

        sigma_clip = SigmaClip(sigma=sigma_value)
        clipped_arrays = sigma_clip(stacked_arrays, axis=0)
        mean_array_clipped = np.nanmean(clipped_arrays, axis=0)

        with rasterio.open(file_list[0]) as src:
            meta = src.meta
        meta.update(count=1)

        with rasterio.open(os.path.join(folder_path, output_filename_mean), 'w', **meta) as dst:
            dst.write(mean_array)

        with rasterio.open(os.path.join(folder_path, output_filename_sigma), 'w', **meta) as dst:
            dst.write(mean_array_clipped)

        fig, axs = plt.subplots(1, 2, figsize=(10, 5))
        axs[0].imshow(np.log1p(mean_array[0]), cmap='turbo')
        axs[0].set_title('Log of Mean Stack')
        axs[1].imshow(np.log1p(mean_array_clipped[0]), cmap='turbo')
        axs[1].set_title('Log of Sigma Clipped')
        plt.savefig(os.path.join(folder_path, 'output_plot.pdf'))
    else:
        print("No arrays with matching shapes were found.")

def main():
    args = parse_arguments()
    process_tif_files(args.folder_path, args.sigma_value, args.threshold_value)

if __name__ == "__main__":
    main()
