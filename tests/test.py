
import subprocess
import os

def test_preprimer_convert():
    # Define the command to run
    command = [
        "preprimer", "convert",
        "--input-format", "varvamp",
        "--primer-info", "tests/test_data/ASFV_long/primers.tsv",
        "--output-format", "artic", "fasta", "sts",
        "--output-folder", "test_output",
        "--prefix", "ASFV",
        "--force"
    ]
    print(" ".join(command))
    # Execute the command
    result = subprocess.run(command, capture_output=True, text=True)

        # Print the output and error if there's a failure
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"stderr: {result.stderr}")
        print(f"stdout: {result.stdout}")

    # Check if the command executed successfully
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Optionally, you can add checks to ensure output files are created and valid
    artic_output_files = [
        os.path.join("test_output/artic/ASFV/V1", "ASFV.scheme.bed"), 
        os.path.join("test_output/artic/ASFV/V1", "ASFV.reference.fasta")]
    fasta_output_file = os.path.join("test_output/fasta/", "ASFV.fasta")
    sts_output_file = os.path.join("test_output/sts/", "ASFV.sts.tsv")
    output_files = artic_output_files + [fasta_output_file, sts_output_file]
    for output_file in output_files:
        assert os.path.exists(output_file), f"Output file {output_file} not created"
    print("Test passed.")

def test_preprimer_convert_change_reference():
    # Define the command to run
    command = [
        "preprimer", "convert",
        "--input-format", "varvamp",
        "--primer-info", "tests/test_data/ASFV_long/primers.tsv",
        "--output-format", "artic", "fasta", "sts",
        "--output-folder", "test_output",
        "--prefix", "ASFV",
        "--reference", "tests/test_data/LR722600.1.fasta",
        "--force"
    ]
    print(" ".join(command))
    # Execute the command
    result = subprocess.run(command, capture_output=True, text=True)

        # Print the output and error if there's a failure
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"stderr: {result.stderr}")
        print(f"stdout: {result.stdout}")

    # Check if the command executed successfully
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Optionally, you can add checks to ensure output files are created and valid
    artic_output_files = [
        os.path.join("test_output/artic/ASFV/V1", "ASFV.scheme.bed"), 
        os.path.join("test_output/artic/ASFV/V1", "ASFV.reference.fasta")]
    fasta_output_file = os.path.join("test_output/fasta/", "ASFV.fasta")
    sts_output_file = os.path.join("test_output/sts/", "ASFV.sts.tsv")
    output_files = artic_output_files + [fasta_output_file, sts_output_file]
    for output_file in output_files:
        assert os.path.exists(output_file), f"Output file {output_file} not created"
    print("Test passed.")

def test_preprimer_align():
    # Define the command to run
    command = [
        "preprimer", "align",
        "--sts-file", "tests/test_data/ASFV.sts.tsv",
        "--output-format", "me-pcr", "exonerate",
        "--reference", "tests/test_data/LR722600.1.fasta",
        "--prefix", "ASFV",
        "--output-folder", "test_output_alignment",
        "--force"
    ]
    print(" ".join(command))
    # Execute the command
    result = subprocess.run(command, capture_output=True, text=True)

        # Print the output and error if there's a failure
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"stderr: {result.stderr}")
        print(f"stdout: {result.stdout}")

    # Check if the command executed successfully
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Optionally, you can add checks to ensure output files are created and valid
    output_folders = ["test_output_alignment/alignment/exonerate" , "test_output_alignment/alignment/mepcr"]
    for output_folder in output_folders:
        assert os.path.exists(output_folder), f"Output folder {output_folder} not created"
    print("Test passed.")

