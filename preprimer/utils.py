import os
import shutil
import re
import tempfile
import subprocess
from pathlib import Path

class FileHandler:
    @staticmethod
    def ask_remove_folder(directory, force=False):
        if not force:
            response = input(f"Do you want to remove the existing folder and create a new '{directory}'? (y/n): ").strip().lower()
            if response == 'y':
                shutil.rmtree(directory)
                print(f"Folder '{directory}' has been removed.")
                return True
            else:
                print("Folder removal canceled.")
                return False
        else:
            shutil.rmtree(directory)
            print(f"Folder '{directory}' has been removed.")
            return True

    @staticmethod
    def check_folder_presence(directory, force=False):
        if not os.path.exists(directory):
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"Output folder {directory} created successfully!")
            return True
        else:
            print(f"Output folder {directory} already exists")
            if FileHandler.ask_remove_folder(directory, force):
                Path(directory).mkdir(parents=True, exist_ok=True)
                print(f"Output folder {directory} created successfully!")
                return True
            else:
                return False

    @staticmethod
    def search_missing_files(files):
        missing_files = []
        for file in files:
            if not os.path.isfile(file):
                missing_files.append(file)
        if missing_files:
            print(f"The following required files are missing:")
            for filename in missing_files:
                print(filename)
            return False
        return True

    @staticmethod
    def copy_file(src, dst):
        shutil.copy(src, dst)

class PrimerWriter:
    @staticmethod
    def write_sts(file_path, amplicons, reference):
        with open(file_path, 'w') as output_file:
            for key in amplicons:
                amplicon_name = key
                seq_fw = ''
                seq_rw = ''
                amplicon_len = ''
                for primer in amplicons[amplicon_name]:
                    if primer['direction'] == 'forward':
                        seq_fw = primer['seq']
                    if primer['direction'] == 'reverse':
                        seq_rw = primer['seq']
                    amplicon_len = primer['amplicon_length']
                output_file.write(f"{amplicon_name}\t{seq_fw}\t{seq_rw}\t{amplicon_len}\n")

    @staticmethod
    def write_fasta(file_path, amplicon_dict):
        with open(file_path, 'w') as output_file:
            for key in amplicon_dict:
                for primer in amplicon_dict[key]:
                    output_file.write(f">{primer['artic_primer_name']}\n{primer['seq']}\n")

    @staticmethod
    def write_artic_scheme(file_path, amplicon_dict):
        with open(file_path, 'w') as output_file:
            for amplicon_name in amplicon_dict:
                for primer in amplicon_dict[amplicon_name]:
                    output_file.write(f"{primer['reference_id']}\t{primer['start']}\t{primer['stop']}\t{primer['artic_primer_name']}\t{primer['pool']}\t{primer['strand']}\n")

    @staticmethod
    def run_exonerate(id, output_path, sequence, reference_genome):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as seq_file:
            seq_file.write(f">{id}\n" + sequence)
            seq_file_path = seq_file.name

        exonerate_command = [
            "exonerate",
            "--model", "affine:local",
            "--query", seq_file_path,
            "--target", reference_genome,
            "--showalignment", "TRUE",
            "--showvulgar", "FALSE",
            "--showcigar", "TRUE",
            "--ryo", "%qas",
            "--percent", "90",
            "--bestn", "1"
        ]
        output_file_path = f"{output_path}/{id}.aln"
        with open(output_file_path, 'w') as output_file:
            subprocess.run(exonerate_command, stdout=output_file, text=True)
        return output_file_path

class AmpliconUpdater:
    @staticmethod
    def find_closest_pair(fw_primer_list, rw_primer_list, old_amplicon_length):
        forward = None
        reverse = None
        min_difference = float('inf')
        length = None
        for fw_dict in fw_primer_list:
            for rw_dict in rw_primer_list:
                start = min(fw_dict['start'], rw_dict['stop'])
                end = max(fw_dict['start'], rw_dict['stop'])
                current_length = end - start

                difference = abs(current_length - old_amplicon_length)

                if difference < min_difference:
                    min_difference = difference
                    length = current_length
                    forward = fw_dict
                    reverse = rw_dict

        return forward, reverse, length

    @staticmethod
    def translate_amplicon_info_to_new_reference(amplicon_info, reference_fasta, output_dir):
        updated_amplicon_info = {}
        
        for amplicon_name, primers in amplicon_info.items():
            old_forward_primer, old_reverse_primer = primers
            old_length = old_forward_primer['amplicon_length']

            alignments = [
                PrimerWriter.run_exonerate(
                    primer['primer_name'], output_dir, primer['seq'], reference_fasta
                )
                for primer in primers
            ]

            forward_primer, reverse_primer, amplicon_length = AmpliconUpdater.find_closest_pair(alignments[0], alignments[1], old_length)

            updated_primers = []
            for old_primer, new_primer in zip(primers, [forward_primer, reverse_primer]):
                updated_primer = old_primer.copy()
                for key in old_primer.keys():
                    if key in new_primer:
                        updated_primer[key] = new_primer[key]
                updated_primer['strand'] = '+' if updated_primer['start'] < updated_primer['stop'] else '-'
                updated_primer['amplicon_length'] = amplicon_length
                updated_primers.append(updated_primer)
            updated_amplicon_info[amplicon_name] = updated_primers
        return updated_amplicon_info

        @staticmethod
        def run_me_pcr(primer_sts_file, reference_genome,  use_temp_file, regular_filepath):
            if use_temp_file:
                # Create a temporary file in the specified folder
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as output_file:
                    output_file_path = output_file.name
            else:
                # Create a regular file in the specified folder
                if regular_filepath is None:
                    raise ValueError("A regular filename must be provided if not using a temporary file.")
                output_file_path = regular_filepath

            # Define me-PCR command
            me_pcr_command = f"me-PCR {primer_sts_file} {reference_genome} O={output_file_path} M=1000"
            # Run me-PCR command
            subprocess.run(me_pcr_command, shell=True)

            return output_file_path

class Aligner:
    @staticmethod
    def run_me_pcr(primer_sts_file, reference_genome,  use_temp_file, regular_filepath):
        if use_temp_file:
            # Create a temporary file in the specified folder
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as output_file:
                output_file_path = output_file.name
        else:
            # Create a regular file in the specified folder
            if regular_filepath is None:
                raise ValueError("A regular filename must be provided if not using a temporary file.")
            output_file_path = regular_filepath

        # Define me-PCR command
        me_pcr_command = f"me-PCR {primer_sts_file} {reference_genome} O={output_file_path} M=1000"
        # Run me-PCR command
        subprocess.run(me_pcr_command, shell=True)

        return output_file_path
