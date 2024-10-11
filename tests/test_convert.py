
import subprocess
import os

def test_preprimer_convert():
    # Define the command to run
    command = [
        "preprimer", "convert",
        "--input-format", "varvamp",
        "--primer-info", "tests/test_data/ASFV_long/primers.tsv",
        "--output-format", "artic",
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
    output_files = [os.path.join("test_output/artic/ASFV/V1", "ASFV.scheme.bed"), os.path.join("test_output/artic/ASFV/V1", "ASFV.reference.fasta")]
    for output_file in output_files:
        assert os.path.exists(output_file), "Output file not created"
    print("Test passed.")
