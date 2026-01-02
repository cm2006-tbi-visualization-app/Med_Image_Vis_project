import os
import glob
import sys
import subprocess

MRI_files = [f for f in glob.glob("*.nii*")
             if f.endswith(('.nii', '.nii.gz'))
             and "_brain" not in f]

if not MRI_files:
    print("No .nii files found in the directory!")
else:
    for f in MRI_files:
        input_file_name = f
        output_file_name = input_file_name.replace(".nii*", "_brain2.nii.gz")
        print(f"Stripping: {input_file_name}")
        try:
            cmd = f"hd-bet -i {input_file_name} -o {output_file_name} -device cpu"
            subprocess.run(cmd, shell=True, check=True)
            print(f"Success! Output saved as: {output_file_name}")
        except Exception as e:
            print(f"An error occurred: {e}")
