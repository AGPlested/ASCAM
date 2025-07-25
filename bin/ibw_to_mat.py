#!/usr/bin/env python

import argparse
import os
import sys

import numpy as np
import scipy.io as sio

script_dir = os.path.dirname(os.path.abspath(__file__))
vendor_dir = os.path.join(script_dir, "..", "vendor")
sys.path.insert(0, vendor_dir)

from ibwpy import ibwpy


def create_parser():
    parser = argparse.ArgumentParser(
        description="Combine Igor Binary Wave files into a single matlab file that "
        "can be read by ASCAM."
    )
    parser.add_argument("current", help="Current .ibw file.")
    parser.add_argument("--command", help="Command Voltage .ibw file.")
    parser.add_argument("--piezo", help="Piezo Voltage .ibw file.")
    parser.add_argument(
        "--sampling-rate",
        dest="sampling_rate",
        default=25000,
        help="Piezo Voltage .ibw file.",
    )
    parser.add_argument("--output", help="Output filename.")

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    # Load the three IBW files
    current_data = ibwpy.load(args.current).array
    if args.command:
        command_data = ibwpy.load(args.command).array
    if args.piezo:
        piezo_data = ibwpy.load(args.piezo).array

    # Sampling parameters
    num_points = current_data.shape[0]  # Number of data points per sweep
    num_sweeps = current_data.shape[1]  # Number of sweeps

    # Create the time vector
    time_vector = np.arange(num_points) / args.sampling_rate

    # Create a dictionary to hold the data for ASCAM
    ascam_data = {
        "c001_Time": time_vector  # Time variable
    }

    # Populate the dictionary with data for each sweep
    for i in range(num_sweeps):
        # For each sweep, assign the corresponding data for Ipatch, Piezo, and Command
        ascam_data[f"c002_Ipatch_{i + 1}"] = current_data[:, i]
        if args.piezo:
            ascam_data[f"c003_Piezo_{i + 1}"] = piezo_data[:, i]
        if args.command:
            ascam_data[f"c004_Command_{i + 1}"] = command_data[:, i]

    # Save the data to a .mat file
    sio.savemat(args.output, ascam_data)


if __name__ == "__main__":
    main()
