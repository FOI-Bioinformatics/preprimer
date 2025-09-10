import os
import re
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .core.security import SecureFileOperations, SecurityError, secure_subprocess_call, InputValidator

logger = logging.getLogger(__name__)

##
# Contains three classes:
# - FileHandler (Security-enhanced)
# - AmpliconUpdater
# - Aligners


class FileHandler:
    """
    Secure file operations handler with path validation.
    
    This class provides secure alternatives to common file operations,
    preventing path traversal and other security vulnerabilities.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize FileHandler with optional base directory restriction.
        
        Args:
            base_dir: Optional base directory to restrict operations to
        """
        self.secure_ops = SecureFileOperations(base_dir)

    @staticmethod
    def ask_remove_folder(directory, force=False):
        """
        Securely ask for confirmation and remove a folder.
        
        Args:
            directory: Directory to remove (validated for security)
            force: Skip confirmation if True
            
        Returns:
            bool: True if folder was removed, False otherwise
        """
        try:
            # Use secure file operations
            secure_ops = SecureFileOperations()
            
            if not force:
                response = (
                    input(
                        f"Do you want to remove the existing folder and create "
                        f"a new '{directory}'? (y/n): "
                    )
                    .strip()
                    .lower()
                )
                if response == "y":
                    secure_ops.safe_remove_tree(directory)
                    logger.info(f"Folder '{directory}' has been removed.")
                    print(f"Folder '{directory}' has been removed.")
                    return True
                else:
                    print("Folder removal canceled.")
                    return False
            else:
                secure_ops.safe_remove_tree(directory)
                logger.info(f"Folder '{directory}' has been removed.")
                print(f"Folder '{directory}' has been removed.")
                return True
                
        except SecurityError as e:
            logger.error(f"Security error removing folder '{directory}': {e}")
            print(f"Error: Cannot remove folder '{directory}' - {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error removing folder '{directory}': {e}")
            print(f"Error removing folder '{directory}': {e}")
            return False

    @staticmethod
    def check_folder_exists(directory, force=False):
        """
        Securely check if folder exists and create or remove as needed.
        
        Args:
            directory: Directory to check/create (validated for security)
            force: Skip confirmation for removal if True
            
        Returns:
            bool: True if folder was created successfully, False otherwise
        """
        try:
            secure_ops = SecureFileOperations()
            
            if not os.path.exists(directory):
                secure_ops.safe_create_directories(directory)
                logger.info(f"Output folder {directory} created successfully!")
                print(f"Output folder {directory} created successfully!")
                return True
            else:
                print(f"Output folder {directory} already exists")
                if FileHandler.ask_remove_folder(directory, force):
                    secure_ops.safe_create_directories(directory)
                    logger.info(f"Output folder {directory} created successfully!")
                    print(f"Output folder {directory} created successfully!")
                    return True
                else:
                    print("Operation cancelled")
                    return False
                    
        except SecurityError as e:
            logger.error(f"Security error with folder '{directory}': {e}")
            print(f"Error: Cannot access folder '{directory}' - {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error with folder '{directory}': {e}")
            print(f"Error with folder '{directory}': {e}")
            return False

    @staticmethod
    def copy_file(src, dst):
        """
        Securely copy a file with path validation.
        
        Args:
            src: Source file path (validated for security)
            dst: Destination file path (validated for security)
            
        Raises:
            SecurityError: If paths are unsafe or operation fails
        """
        try:
            secure_ops = SecureFileOperations()
            
            # Validate and sanitize paths
            src_path = secure_ops.validator.sanitize_path(src)
            dst_path = secure_ops.validator.sanitize_path(dst)
            
            # Ensure source file exists and is readable
            if not src_path.exists():
                raise SecurityError(f"Source file does not exist: {src_path}")
            
            if not src_path.is_file():
                raise SecurityError(f"Source is not a file: {src_path}")
            
            # Ensure destination directory exists
            dst_dir = dst_path.parent
            if not dst_dir.exists():
                secure_ops.safe_create_directories(dst_dir)
            
            # Perform the copy operation
            import shutil
            shutil.copy2(src_path, dst_path)
            logger.info(f"File copied successfully: {src_path} -> {dst_path}")
            
        except SecurityError:
            raise  # Re-raise security errors
        except Exception as e:
            raise SecurityError(f"Failed to copy file: {e}") from e


# ___________________________________________________________
# ___________________________________________________________
class AmpliconUpdater:
    @staticmethod
    def find_closest_pair(fw_primer_list, rw_primer_list, old_amplicon_length):
        forward = None
        reverse = None
        min_difference = float("inf")
        length = None
        for fw_dict in fw_primer_list:
            for rw_dict in rw_primer_list:
                start = min(fw_dict["start"], rw_dict["stop"])
                end = max(fw_dict["start"], rw_dict["stop"])
                current_length = end - start

                difference = abs(current_length - old_amplicon_length)

                if difference < min_difference:
                    min_difference = difference
                    length = current_length
                    forward = fw_dict
                    reverse = rw_dict

        return forward, reverse, length

    @staticmethod
    def translate_amplicon_info_to_new_reference(
        amplicon_info,
        reference_fasta,
        output_dir,
        aligner,
        force=False,
    ):
        updated_amplicon_info = {}
        for amplicon_name, primers in amplicon_info.items():
            old_forward_primer, old_reverse_primer = primers
            old_length = old_forward_primer["amplicon_length"]
            alignments = []

            for primer in primers:
                primer_name = primer["primer_name"]
                primer_seq = primer["seq"]
                parsed_alignment = ""
                if aligner == "exonerate":
                    alignment_output = Aligner.run_exonerate(
                        primer_name, output_dir, primer_seq, reference_fasta
                    )
                    parsed_alignment = Aligner.parse_exonerate_output(alignment_output)
                elif aligner == "blast":
                    alignment_output = Aligner.run_blast(
                        primer_name, output_dir, primer_seq, reference_fasta, "6"
                    )
                    parsed_alignment = Aligner.parse_blast_output(alignment_output)
                # If parsing exonerate output fails i.e. no alignments found
                if not parsed_alignment:
                    print(
                        f"\nNo alignment found for primer {primer_name} "
                        f"in amplicon {amplicon_name} to {reference_fasta}."
                    )
                    if not force:
                        user_input = input("Do you want to continue anyway?  (y/n): ")
                        if user_input.lower() == "n":
                            print("Program will exit. Try a different reference")
                            exit()
                    else:
                        print("Option --force excludes by default.")
                    print(f'Amplicon named "{amplicon_name}" excluded.\n')
                elif parsed_alignment:
                    alignments.append(parsed_alignment)

            # A succefull alignment where both primers have have one ore more
            # hits
            if len(alignments) == 2:
                forward_parsed, reverse_parsed = alignments
                if forward_parsed and reverse_parsed:
                    forward_primer, reverse_primer, amplicon_length = (
                        AmpliconUpdater.find_closest_pair(
                            forward_parsed, reverse_parsed, old_length
                        )
                    )
                    updated_primers = []
                    for old_primer, new_primer in zip(
                        primers, [forward_primer, reverse_primer]
                    ):
                        updated_primer = old_primer.copy()
                        for key in old_primer.keys():
                            if key in new_primer:
                                updated_primer[key] = new_primer[key]
                        updated_primer["strand"] = (
                            "+"
                            if updated_primer["start"] < updated_primer["stop"]
                            else "-"
                        )
                        updated_primer["amplicon_length"] = amplicon_length
                        updated_primers.append(updated_primer)

                    if updated_primers:
                        updated_amplicon_info[amplicon_name] = updated_primers
            elif len(alignments) == 0:
                continue

        return updated_amplicon_info


# ___________________________________________________________
# ___________________________________________________________
class Aligner:
    @staticmethod
    def run_me_pcr(primer_sts_file, reference_genome, use_temp_file, regular_filepath):
        """
        Securely execute me-PCR command with input validation.
        
        Args:
            primer_sts_file: Path to primer STS file
            reference_genome: Path to reference genome
            use_temp_file: Whether to use temporary file for output
            regular_filepath: Regular file path if not using temp file
            
        Returns:
            str: Path to output file
            
        Raises:
            SecurityError: If paths are unsafe or command fails
        """
        try:
            secure_ops = SecureFileOperations()
            
            # Validate and sanitize input paths
            primer_path = secure_ops.validator.sanitize_path(primer_sts_file)
            reference_path = secure_ops.validator.sanitize_path(reference_genome)
            
            if use_temp_file:
                # Create a temporary file in the specified folder
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as output_file:
                    output_file_path = output_file.name
            else:
                # Create a regular file in the specified folder
                if regular_filepath is None:
                    raise ValueError(
                        "A regular filename must be provided if not using a temporary file."
                    )
                output_file_path = str(secure_ops.validator.sanitize_path(regular_filepath))

            # Define me-PCR command as list (safer than shell=True)
            me_pcr_command = [
                "me-PCR",
                str(primer_path),
                str(reference_path),
                f"O={output_file_path}",
                "M=1000"
            ]
            
            # Run me-PCR command securely
            result = secure_subprocess_call(me_pcr_command)
            
            if result.returncode != 0:
                logger.error(f"me-PCR failed with return code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                raise SecurityError(f"me-PCR execution failed: {result.stderr}")
            
            logger.info(f"me-PCR completed successfully, output: {output_file_path}")
            return output_file_path
            
        except SecurityError:
            raise  # Re-raise security errors
        except Exception as e:
            raise SecurityError(f"Failed to run me-PCR: {e}") from e

    @staticmethod
    def run_exonerate(id, output_path, sequence, reference_genome):
        """
        Securely execute exonerate alignment with input validation.
        
        Args:
            id: Sequence identifier
            output_path: Directory for output files
            sequence: Primer sequence to align
            reference_genome: Path to reference genome file
            
        Returns:
            str: Path to alignment output file
            
        Raises:
            SecurityError: If inputs are unsafe or command fails
        """
        try:
            secure_ops = SecureFileOperations()
            input_validator = InputValidator()
            
            # Validate inputs
            input_validator.validate_amplicon_name(id)
            input_validator.validate_primer_sequence(sequence)
            
            # Validate and sanitize paths
            output_dir = secure_ops.validator.sanitize_path(output_path)
            reference_path = secure_ops.validator.sanitize_path(reference_genome)
            
            # Create secure temporary sequence file
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".fasta") as seq_file:
                seq_file.write(f">{id}\n{sequence}\n")
                seq_file_path = seq_file.name
            
            try:
                # Validate sequence file path
                seq_path = secure_ops.validator.sanitize_path(seq_file_path)
                
                exonerate_command = [
                    "exonerate",
                    "--model",
                    "affine:local",
                    "--query",
                    str(seq_path),
                    "--target",
                    str(reference_path),
                    "--showalignment",
                    "TRUE",
                    "--showvulgar",
                    "FALSE",
                    "--showcigar",
                    "TRUE",
                    "--ryo",
                    "%qas",
                    "--percent",
                    "90",
                    "--bestn",
                    "1",
                ]
                
                # Create secure output file path
                output_file_path = output_dir / f"{id}.aln"
                
                # Run exonerate securely
                with secure_ops.safe_open_file(output_file_path, "w") as output_file:
                    result = secure_subprocess_call(exonerate_command)
                    output_file.write(result.stdout)
                
                if result.returncode != 0:
                    logger.warning(f"Exonerate returned non-zero exit code {result.returncode}")
                    logger.warning(f"Error output: {result.stderr}")
                
                logger.info(f"Exonerate alignment completed for {id}")
                return str(output_file_path)
                
            finally:
                # Clean up temporary sequence file
                try:
                    os.unlink(seq_file_path)
                except OSError:
                    pass  # File might already be deleted
                    
        except (SecurityError, ValueError):
            raise  # Re-raise security and validation errors
        except Exception as e:
            raise SecurityError(f"Failed to run exonerate alignment: {e}") from e

    @staticmethod
    def parse_exonerate_output(output_file_path):
        alignments = []
        alignment = {}

        with open(output_file_path, "r") as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()

            if line.startswith("cigar:"):
                # Process cigar line and add alignment to the list
                cigar_parts = line.split()
                if len(cigar_parts) >= 8:
                    alignment["primer_name"] = cigar_parts[1]
                    alignment["query_start"] = int(cigar_parts[2])
                    alignment["query_end"] = int(cigar_parts[3])
                    alignment["reference_id"] = cigar_parts[5]
                    alignment["start"] = int(cigar_parts[6])
                    alignment["stop"] = int(cigar_parts[7])
                    alignment["strand"] = cigar_parts[8]
                    alignment["score"] = float(cigar_parts[9])
                    alignment["cigar"] = f"{cigar_parts[10]}{cigar_parts[11]}"

                    # Add alignment to list if all fields are present
                    if all(
                        key in alignment
                        for key in [
                            "query_start",
                            "query_end",
                            "start",
                            "stop",
                            "score",
                        ]
                    ):
                        alignments.append(alignment)
                        alignment = {}
        return alignments

    @staticmethod
    def run_blast(id, output_path, sequence, reference_genome, format):
        """
        Securely execute BLAST alignment with input validation.
        
        Args:
            id: Sequence identifier
            output_path: Directory for output files
            sequence: Primer sequence to align
            reference_genome: Path to reference genome file
            format: BLAST output format
            
        Returns:
            str: Path to BLAST output file
            
        Raises:
            SecurityError: If inputs are unsafe or command fails
        """
        try:
            secure_ops = SecureFileOperations()
            input_validator = InputValidator()
            
            # Validate inputs
            input_validator.validate_amplicon_name(id)
            input_validator.validate_primer_sequence(sequence)
            
            if format not in ['6', '7', '10', '11']:  # Valid BLAST tabular formats
                raise SecurityError(f"Invalid BLAST format: {format}")
                
            # Validate and sanitize paths
            output_dir = secure_ops.validator.sanitize_path(output_path)
            reference_path = secure_ops.validator.sanitize_path(reference_genome)
            
            if not reference_path.exists():
                raise SecurityError(f"Reference genome file not found: {reference_path}")
                
            # Create secure temporary sequence file
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".fasta") as seq_file:
                logger.info(f"Analyzing sequence: {id}")
                seq_file.write(f">{id}\n{sequence}\n")
                seq_file_path = seq_file.name
            
            try:
                # Validate sequence file path
                seq_path = secure_ops.validator.sanitize_path(seq_file_path)
                
                # Prepare BLAST database paths securely
                blast_db_prefix = reference_path.stem
                db_dir = output_dir / "db"
                secure_ops.safe_create_directories(db_dir)
                blastdb_output = db_dir / blast_db_prefix
                
                # Create BLAST database if needed
                db_check_file = Path(str(blastdb_output) + ".nhr")
                if not db_check_file.exists():
                    blastdb_command = [
                        "makeblastdb",
                        "-in",
                        str(reference_path),
                        "-dbtype",
                        "nucl",
                        "-out",
                        str(blastdb_output),
                    ]
                    
                    result = secure_subprocess_call(blastdb_command)
                    if result.returncode != 0:
                        raise SecurityError(f"Failed to create BLAST database: {result.stderr}")
                    
                    logger.info("BLAST database created successfully")
                
                # Create secure output file path
                output_file_path = output_dir / f"{id}.blast"
                
                # Run BLAST alignment securely
                blast_command = [
                    "blastn",
                    "-query",
                    str(seq_path),
                    "-db",
                    str(blastdb_output),
                    "-out",
                    str(output_file_path),
                    "-outfmt",
                    format,
                    "-evalue",
                    "1e-4",
                    "-task",
                    "blastn-short",
                ]
                
                result = secure_subprocess_call(blast_command)
                if result.returncode != 0:
                    logger.warning(f"BLAST returned non-zero exit code {result.returncode}")
                    logger.warning(f"Error output: {result.stderr}")
                    raise SecurityError(f"BLAST alignment failed: {result.stderr}")
                
                logger.info(f"BLAST alignment completed for {id}")
                return str(output_file_path)
                
            finally:
                # Clean up temporary sequence file
                try:
                    os.unlink(seq_file_path)
                except OSError:
                    pass  # File might already be deleted
                    
        except (SecurityError, ValueError):
            raise  # Re-raise security and validation errors
        except Exception as e:
            raise SecurityError(f"Failed to run BLAST alignment: {e}") from e

    @staticmethod
    def parse_blast_output(output_file_path):
        alignments = []

        # Define column indices based on BLAST's tabular output
        column_indices = {
            "query_id": 0,
            "subject_id": 1,
            "percent_identity": 2,
            "alignment_length": 3,
            "mismatches": 4,
            "gap_opens": 5,
            "query_start": 6,
            "query_end": 7,
            "subject_start": 8,
            "subject_end": 9,
            "evalue": 10,
            "bit_score": 11,
        }

        with open(output_file_path, "r") as file:
            for line in file:
                parts = line.strip().split("\t")
                if len(parts) >= 12:
                    alignment = {
                        "primer_name": parts[column_indices["query_id"]],
                        "reference_id": parts[column_indices["subject_id"]],
                        "query_start": int(parts[column_indices["query_start"]]),
                        "query_end": int(parts[column_indices["query_end"]]),
                        "start": int(parts[column_indices["subject_start"]]),
                        "stop": int(parts[column_indices["subject_end"]]),
                        "percent_identity": float(
                            parts[column_indices["percent_identity"]]
                        ),
                        "alignment_length": int(
                            parts[column_indices["alignment_length"]]
                        ),
                        "score": float(parts[column_indices["bit_score"]]),
                        "evalue": float(parts[column_indices["evalue"]]),
                    }
                    alignments.append(alignment)

        return alignments

    @staticmethod
    def contains_non_atgc(string):
        # Define a regular expression pattern to match any character except
        # 'a', 't', 'c', and 'g'
        pattern = re.compile(r"[^atcg]", re.IGNORECASE)
        # Search for any non-ATCG characters in the string
        non_atgc_chars = pattern.findall(string)
        # If a match is found, return True (indicating presence of non-ATCG
        # characters), otherwise return False
        return non_atgc_chars
