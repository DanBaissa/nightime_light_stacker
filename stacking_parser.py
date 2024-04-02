import rasterio
import numpy as np
import os
import glob
from astropy.stats import SigmaClip
import matplotlib.pyplot as plt
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process .tif files with options for mean stacking, sigma clipping stacking, or both.")
    parser.add_argument("--folder-path", required=True, help="Path to the folder containing .tif files.")
    parser.add_argument("--sigma-value", type=float, default=None, help="Sigma value for sigma clipping. Required if --sigma-stacking is enabled.")
    parser.add_argument("--threshold-value", type=float, required=True, help="Threshold value to set numbers above this to NA.")
    parser.add_argument("--mean-stacking", action='store_true', help="Enable mean stacking.")
    parser.add_argument("--sigma-stacking", action='store_true', help="Enable sigma clipping stacking.")
    parser.add_argument("--iters", type=int, default=5, help="Number of iterations for sigma clipping. Required if --sigma-stacking is enabled.")

    args = parser.parse_args()

    # Enforce sigma-value and iters to be specified if sigma-stacking is enabled
    if args.sigma_stacking and args.sigma_value is None:
        parser.error("--sigma-value is required when --sigma-stacking is enabled.")
    if args.sigma_stacking and args.iters is None:  # This check is technically redundant since iters has a default value
        parser.error("--iters is required when --sigma-stacking is enabled.")

    return args


def process_tif_files(folder_path, sigma_value, threshold_value, mean_stacking, sigma_stacking, maxiters):
    if not mean_stacking and not sigma_stacking:
        print("Please enable at least one stacking method: mean stacking or sigma clipping stacking.")
        return

    file_list = glob.glob(os.path.join(folder_path, '*.tif'))
    data_arrays = []
    reference_shape = None

    for file in file_list:
        with rasterio.open(file) as src:
            data = src.read().astype('float32')
            data[data > threshold_value] = np.nan
            if reference_shape is None:
                reference_shape = data.shape
            if data.shape == reference_shape:
                data_arrays.append(data)
            else:
                print(f"Skipping array from {file} due to shape mismatch: expected {reference_shape}, got {data.shape}")

    if len(data_arrays) > 0:
        stacked_arrays = np.stack(data_arrays, axis=0)

        # Prepare for plotting
        fig, axs = plt.subplots(1, 2 if mean_stacking and sigma_stacking else 1, figsize=(10, 5))
        if not isinstance(axs, np.ndarray):
            axs = [axs]

        plot_idx = 0  # Index to track which subplot to use

        if mean_stacking:
            mean_array = np.nanmean(stacked_arrays, axis=0)
            with rasterio.open(file_list[0]) as src:
                meta = src.meta
            meta.update(count=1)
            with rasterio.open(os.path.join(folder_path, 'output_mean.tif'), 'w', **meta) as dst:
                dst.write(mean_array)

            # Plot mean stacking result
            axs[plot_idx].imshow(np.log1p(mean_array[0]), cmap='turbo')
            axs[plot_idx].set_title('Log of Mean Stack')
            plot_idx += 1

        if sigma_stacking:
            sigma_clip = SigmaClip(sigma=sigma_value, maxiters=maxiters)
            clipped_arrays = sigma_clip(stacked_arrays, axis=0)
            mean_array_clipped = np.nanmean(clipped_arrays, axis=0)
            with rasterio.open(file_list[0]) as src:
                meta = src.meta
            meta.update(count=1)
            with rasterio.open(os.path.join(folder_path, 'output_sigma_clipped.tif'), 'w', **meta) as dst:
                dst.write(mean_array_clipped)

            # Plot sigma clipping stacking result
            axs[plot_idx].imshow(np.log1p(mean_array_clipped[0]), cmap='turbo')
            axs[plot_idx].set_title('Log of Sigma Clipped')

        # Save the plot
        plt.tight_layout()
        plt.savefig(os.path.join(folder_path, 'output_plot.pdf'))

    else:
        print("No arrays with matching shapes were found.")


def main():
    args = parse_arguments()
    process_tif_files(args.folder_path, args.sigma_value, args.threshold_value, args.mean_stacking, args.sigma_stacking, args.iters)

if __name__ == "__main__":
    main()
